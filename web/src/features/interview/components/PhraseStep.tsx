import { useEffect, useRef, useState } from "react";

import { playPrompt, stopPlayback, type Prompt } from "../../../shared/lib/audio";

interface PhraseStepProps {
  prompt: Prompt;
  onDone: () => void;
}

export function PhraseStep({ prompt, onDone }: PhraseStepProps): React.JSX.Element {
  const [error, setError] = useState<string | null>(null);
  const onDoneRef = useRef(onDone);

  useEffect(() => {
    onDoneRef.current = onDone;
  }, [onDone]);

  useEffect(() => {
    let cancelled = false;
    async function run(): Promise<void> {
      try {
        await playPrompt(prompt);
        if (!cancelled) {
          onDoneRef.current();
        }
      } catch (playError) {
        if (!cancelled) {
          setError(playError instanceof Error ? playError.message : String(playError));
        }
      }
    }
    void run();
    return () => {
      cancelled = true;
      stopPlayback();
    };
  }, [prompt]);

  if (error) {
    return (
      <div className="flex flex-col items-center gap-2">
        <p className="text-sm text-red-700">{error}</p>
        <button
          type="button"
          className="rounded-lg border border-gray-400 px-4 py-2"
          onClick={() => onDoneRef.current()}
        >
          続ける
        </button>
      </div>
    );
  }
  return <p className="text-gray-600">面接官が話しています…</p>;
}
