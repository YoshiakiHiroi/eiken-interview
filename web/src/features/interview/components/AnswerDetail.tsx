import { useState } from "react";

import { ErrorMessage } from "../../../shared/components/ErrorMessage";
import { ProblemCard } from "../../../shared/components/ProblemCard";
import type { Answer, GradePart, ProblemSet } from "../../../shared/types/api";
import { findQuestion } from "../flow/interviewFlow";
import { submitAnswer, type PartAnswer } from "../services/interviewApi";
import { PartAnswerFlow } from "./PartAnswerFlow";

interface AnswerDetailProps {
  sessionId: string;
  part: GradePart;
  problemSet: ProblemSet;
  answer: Answer | undefined;
  onUpdated: () => void;
}

export function AnswerDetail({
  sessionId,
  part,
  problemSet,
  answer,
  onUpdated,
}: AnswerDetailProps): React.JSX.Element {
  const [isRetrying, setIsRetrying] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function resubmit(partAnswer: PartAnswer): Promise<void> {
    setIsSending(true);
    setError(null);
    try {
      await submitAnswer(sessionId, partAnswer);
      setIsRetrying(false);
      onUpdated();
    } catch (submitError) {
      setError(submitError);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <details className="rounded-xl border border-gray-300 bg-white p-3">
      <summary className="flex cursor-pointer justify-between font-semibold">
        <span>{part.label}</span>
        <span className="tabular-nums">
          {answer?.score ?? "－"} / {part.max_score}
        </span>
      </summary>

      <div className="mt-3 flex flex-col gap-3 text-sm">
        {!answer && <p className="text-gray-500">回答がありません。</p>}
        {answer?.evaluation_error && (
          <p className="rounded-lg bg-yellow-50 p-2 text-yellow-800">
            採点に失敗しました。「もう一度答える」で再採点できます。
          </p>
        )}
        {answer && (
          <>
            <audio
              controls
              src={answer.audio_url}
              className="w-full"
            />
            {answer.follow_up_audio_url && (
              <audio
                controls
                src={answer.follow_up_audio_url}
                className="w-full"
              />
            )}
            <Section title="文字起こし">{answer.transcript}</Section>
            <Section title="講評">{answer.feedback_ja}</Section>
            <Section title="模範解答">{answer.model_answer}</Section>
            {answer.issue_tags.length > 0 && (
              <ul className="flex flex-wrap gap-1">
                {answer.issue_tags.map((tag) => (
                  <li
                    key={tag}
                    className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
                  >
                    {tag}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}

        {isSending && <p className="text-gray-600">採点しています…</p>}
        <ErrorMessage error={error} />
        {isRetrying && !isSending ? (
          <div className="flex flex-col gap-3">
            <ProblemCard
              card={part.card}
              problemSet={problemSet}
            />
            <PartAnswerFlow
              part={part}
              question={findQuestion(problemSet, part)}
              onComplete={(partAnswer) => void resubmit(partAnswer)}
            />
          </div>
        ) : (
          !isSending && (
            <button
              type="button"
              className="rounded-lg border border-blue-600 py-2 font-semibold text-blue-700"
              onClick={() => setIsRetrying(true)}
            >
              もう一度答える
            </button>
          )
        )}
      </div>
    </details>
  );
}

interface SectionProps {
  title: string;
  children: string | null;
}

function Section({ title, children }: SectionProps): React.JSX.Element | null {
  if (!children) {
    return null;
  }
  return (
    <div>
      <h3 className="text-xs font-semibold text-gray-500">{title}</h3>
      <p className="whitespace-pre-wrap">{children}</p>
    </div>
  );
}
