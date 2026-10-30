import { useCallback, useEffect, useRef, useState } from "react";

import { Elapsed } from "../../../shared/components/Timer";
import { useRecorder, type Recording } from "../../../shared/hooks/useRecorder";
import { playPrompt, stopPlayback, type Prompt } from "../../../shared/lib/audio";
import type { GradePart, Question, YesNo } from "../../../shared/types/api";
import { followUpPrompt, questionPrompt } from "../flow/interviewFlow";
import type { PartAnswer } from "../services/interviewApi";

type Stage =
  | { name: "playing"; round: "main" | "followUp" }
  | { name: "recording"; round: "main" | "followUp"; startedAt: number }
  | { name: "yesNo" }
  | { name: "promptFailed"; round: "main" | "followUp"; message: string };

interface PartAnswerFlowProps {
  part: GradePart;
  question: Question | null;
  onComplete: (answer: PartAnswer) => void;
}

export function PartAnswerFlow({
  part,
  question,
  onComplete,
}: PartAnswerFlowProps): React.JSX.Element {
  const recorder = useRecorder();
  const [stage, setStage] = useState<Stage>({ name: "playing", round: "main" });
  const [yesNo, setYesNo] = useState<YesNo | null>(null);
  const mainRecordingRef = useRef<Recording | null>(null);
  const replayCountRef = useRef(0);

  const promptFor = useCallback(
    (round: "main" | "followUp"): Prompt | null =>
      round === "main" ? questionPrompt(question) : yesNo && followUpPrompt(question, yesNo),
    [question, yesNo],
  );

  const startRecording = recorder.start;
  const playing = stage.name === "playing" ? stage.round : null;
  useEffect(() => {
    if (playing === null) {
      return;
    }
    const round = playing;
    let cancelled = false;
    async function playThenRecord(): Promise<void> {
      const prompt = promptFor(round);
      try {
        if (prompt) {
          await playPrompt(prompt);
        }
      } catch (error) {
        if (!cancelled) {
          setStage({
            name: "promptFailed",
            round,
            message: error instanceof Error ? error.message : String(error),
          });
        }
        return;
      }
      if (cancelled) {
        return;
      }
      await startRecording();
      setStage({ name: "recording", round, startedAt: performance.now() });
    }
    void playThenRecord();
    return () => {
      cancelled = true;
      stopPlayback();
    };
  }, [playing, promptFor, startRecording]);

  async function finishRound(round: "main" | "followUp"): Promise<void> {
    const recording = await recorder.stop();
    if (round === "main" && part.follow_up) {
      mainRecordingRef.current = recording;
      setStage({ name: "yesNo" });
      return;
    }
    const main = round === "main" ? recording : mainRecordingRef.current;
    if (!main) {
      throw new Error("main recording is missing");
    }
    onComplete({
      partId: part.id,
      main,
      followUp: round === "followUp" ? recording : null,
      yesNo,
      replayCount: replayCountRef.current,
    });
  }

  async function replay(round: "main" | "followUp"): Promise<void> {
    replayCountRef.current += 1;
    await recorder.stop();
    setStage({ name: "playing", round });
  }

  function chooseYesNo(choice: YesNo): void {
    setYesNo(choice);
    setStage({ name: "playing", round: "followUp" });
  }

  if (recorder.status === "error") {
    return (
      <p
        role="alert"
        className="rounded-lg bg-red-50 p-3 text-sm text-red-700"
      >
        {recorder.error}
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      {stage.name === "playing" && <p className="text-gray-600">面接官が話しています…</p>}

      {stage.name === "promptFailed" && (
        <div className="flex flex-col items-center gap-2">
          <p className="text-sm text-red-700">{stage.message}</p>
          <button
            type="button"
            className="rounded-lg border border-gray-400 px-4 py-2"
            onClick={() => setStage({ name: "playing", round: stage.round })}
          >
            質問を再生する
          </button>
        </div>
      )}

      {stage.name === "recording" && (
        <>
          <p className="flex items-center gap-2 font-semibold text-red-600">
            <span className="inline-block size-3 animate-pulse rounded-full bg-red-600" />
            録音中 <Elapsed startedAt={stage.startedAt} />
          </p>
          <button
            type="button"
            className="w-full rounded-xl bg-blue-600 py-4 text-lg font-bold text-white"
            onClick={() => void finishRound(stage.round)}
          >
            回答終了
          </button>
          {promptFor(stage.round) && (
            <button
              type="button"
              className="text-sm text-blue-700 underline"
              onClick={() => void replay(stage.round)}
            >
              もう一度質問を聞く
            </button>
          )}
        </>
      )}

      {stage.name === "yesNo" && (
        <div className="flex w-full flex-col gap-2">
          <p className="text-center text-sm text-gray-600">最初に答えたのはどちらですか？</p>
          <div className="flex gap-3">
            <button
              type="button"
              className="flex-1 rounded-xl border-2 border-blue-600 py-3 font-bold text-blue-700"
              onClick={() => chooseYesNo("yes")}
            >
              Yes
            </button>
            <button
              type="button"
              className="flex-1 rounded-xl border-2 border-blue-600 py-3 font-bold text-blue-700"
              onClick={() => chooseYesNo("no")}
            >
              No
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
