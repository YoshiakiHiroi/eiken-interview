import { useCallback, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router";

import { ErrorMessage } from "../../../shared/components/ErrorMessage";
import { ProblemCard } from "../../../shared/components/ProblemCard";
import { Timer } from "../../../shared/components/Timer";
import { useGradeStore, useSelectedGrade } from "../../grades/store/gradeStore";
import { PartAnswerFlow } from "../components/PartAnswerFlow";
import { PhraseStep } from "../components/PhraseStep";
import { findQuestion, phrasePrompt } from "../flow/interviewFlow";
import { hasPendingSubmissions, useInterviewStore } from "../store/interviewStore";

export function InterviewPage(): React.JSX.Element {
  const loadGrades = useGradeStore((state) => state.load);
  const gradeError = useGradeStore((state) => state.error);
  const selectedGrade = useSelectedGrade();
  const store = useInterviewStore();
  const reset = useInterviewStore((state) => state.reset);
  const navigate = useNavigate();
  const { phase, grade, problemSet, steps, stepIndex, submissions } = store;
  const step = steps[stepIndex];

  useEffect(() => {
    void loadGrades();
  }, [loadGrades]);

  useEffect(() => reset, [reset]);

  const finishAndShowResult = useCallback(async (): Promise<void> => {
    const session = await useInterviewStore.getState().finish();
    if (session) {
      await navigate(`/interview/result/${session.id}`);
    }
  }, [navigate]);

  const pending = hasPendingSubmissions(submissions);
  useEffect(() => {
    if (phase === "finishing" && !pending) {
      void finishAndShowResult();
    }
  }, [phase, pending, finishAndShowResult]);

  const prompt = useMemo(
    () =>
      grade && problemSet && step?.kind === "phrase"
        ? phrasePrompt(grade, problemSet, step.phraseKey)
        : null,
    [grade, problemSet, step],
  );

  if (phase === "idle" || phase === "error") {
    return (
      <div className="flex flex-col gap-4">
        <ErrorMessage error={store.error ?? gradeError} />
        <p className="text-sm text-gray-600">
          音声が流れます。静かな場所で、マイクを使える状態にしてください。
        </p>
        <button
          type="button"
          disabled={!selectedGrade}
          className="rounded-xl bg-blue-600 py-4 text-lg font-bold text-white disabled:opacity-50"
          onClick={() => selectedGrade && void store.start(selectedGrade)}
        >
          面接を始める（{selectedGrade?.label ?? "…"}）
        </button>
        <Link
          to="/"
          className="text-center text-sm text-gray-500 underline"
        >
          ホームに戻る
        </Link>
      </div>
    );
  }

  if (phase === "preparing" || !grade || !problemSet) {
    return <p className="text-center text-gray-500">問題を準備しています…</p>;
  }

  if (phase === "finishing" || phase === "finished") {
    const failed = Object.values(submissions).filter((item) => item.status === "failed");
    return (
      <div className="flex flex-col gap-4">
        <p className="text-center font-semibold">採点しています…</p>
        <ul className="flex flex-col gap-1 text-sm">
          {Object.entries(submissions).map(([partId, submission]) => (
            <li key={partId}>
              {grade.parts.find((part) => part.id === partId)?.label ?? partId}:{" "}
              {{ sending: "採点中", done: "完了", failed: "送信失敗" }[submission.status]}
            </li>
          ))}
        </ul>
        {failed.map((submission) => (
          <div
            key={submission.answer.partId}
            className="flex flex-col gap-1"
          >
            <ErrorMessage error={submission.error} />
            <button
              type="button"
              className="rounded-lg border border-gray-400 py-2"
              onClick={() => void store.submit(submission.answer)}
            >
              {submission.answer.partId} を再送する
            </button>
          </div>
        ))}
        <ErrorMessage error={store.error} />
        {store.error !== null && !pending && (
          <button
            type="button"
            className="rounded-lg border border-gray-400 py-2"
            onClick={() => void finishAndShowResult()}
          >
            結果の集計をやり直す
          </button>
        )}
      </div>
    );
  }

  if (!step) {
    return <p className="text-center text-gray-500">…</p>;
  }

  return (
    <div className="flex min-h-[calc(100dvh-2rem)] flex-col gap-4">
      <header className="flex items-center justify-between border-b pb-2">
        <span className="font-semibold">{step.part?.label ?? "入室"}</span>
        {step.kind === "timer" && (
          <Timer
            key={stepIndex}
            seconds={step.seconds}
            onDone={store.next}
          />
        )}
      </header>

      <main className="flex-1">
        <ProblemCard
          card={step.card}
          problemSet={problemSet}
        />
      </main>

      <footer className="pb-4">
        {step.kind === "phrase" && prompt && (
          <PhraseStep
            key={stepIndex}
            prompt={prompt}
            onDone={store.next}
          />
        )}
        {step.kind === "timer" && <p className="text-center text-gray-600">黙読してください</p>}
        {step.kind === "answer" && (
          <PartAnswerFlow
            key={stepIndex}
            part={step.part}
            question={findQuestion(problemSet, step.part)}
            onComplete={(answer) => {
              void store.submit(answer);
              store.next();
            }}
          />
        )}
      </footer>
    </div>
  );
}
