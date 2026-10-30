import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";

import { ErrorMessage } from "../../../shared/components/ErrorMessage";
import { ScoreCard } from "../../../shared/components/ScoreCard";
import type { ProblemSet, Session } from "../../../shared/types/api";
import { useGradeConfig, useGradeStore } from "../../grades/store/gradeStore";
import { AnswerDetail } from "../components/AnswerDetail";
import { scoredParts } from "../flow/interviewFlow";
import { fetchSession, fetchSet } from "../services/interviewApi";

export function ResultPage(): React.JSX.Element {
  const { sessionId = "" } = useParams();
  const loadGrades = useGradeStore((state) => state.load);
  const [session, setSession] = useState<Session | null>(null);
  const [problemSet, setProblemSet] = useState<ProblemSet | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [version, setVersion] = useState(0);
  const grade = useGradeConfig(session?.grade ?? null);

  useEffect(() => {
    void loadGrades();
  }, [loadGrades]);

  useEffect(() => {
    let cancelled = false;
    async function load(): Promise<void> {
      try {
        const loaded = await fetchSession(sessionId);
        const loadedSet = await fetchSet(loaded.set_id);
        if (!cancelled) {
          setSession(loaded);
          setProblemSet(loadedSet);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError);
        }
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [sessionId, version]);

  if (error) {
    return <ErrorMessage error={error} />;
  }
  if (!session || !problemSet || !grade) {
    return <p className="text-center text-gray-500">読み込み中…</p>;
  }

  const answers = new Map(session.answers.map((answer) => [answer.part, answer]));
  return (
    <div className="flex flex-col gap-4 pb-8">
      <h1 className="text-lg font-bold">結果（{grade.label}）</h1>
      <ScoreCard
        grade={grade}
        session={session}
      />
      {session.attitude?.feedback_ja && (
        <section className="rounded-xl border border-gray-300 bg-white p-3 text-sm">
          <h2 className="mb-1 font-semibold">アティチュード</h2>
          <p>{session.attitude.feedback_ja}</p>
        </section>
      )}
      {scoredParts(grade)
        .filter((part) => session.mode === "full" || answers.has(part.id))
        .map((part) => (
          <AnswerDetail
            key={part.id}
            sessionId={session.id}
            part={part}
            problemSet={problemSet}
            answer={answers.get(part.id)}
            onUpdated={() => setVersion((current) => current + 1)}
          />
        ))}
      <Link
        to="/"
        className="text-center text-sm text-gray-500 underline"
      >
        ホームに戻る
      </Link>
    </div>
  );
}
