import { useEffect, useRef, useState } from "react";

interface TimerProps {
  seconds: number;
  onDone: () => void;
}

export function Timer({ seconds, onDone }: TimerProps): React.JSX.Element {
  const [remaining, setRemaining] = useState(seconds);
  const onDoneRef = useRef(onDone);

  useEffect(() => {
    onDoneRef.current = onDone;
  }, [onDone]);

  useEffect(() => {
    const startedAt = performance.now();
    const id = window.setInterval(() => {
      const left = Math.max(0, seconds - Math.floor((performance.now() - startedAt) / 1000));
      setRemaining(left);
      if (left === 0) {
        window.clearInterval(id);
        onDoneRef.current();
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [seconds]);

  return (
    <span
      className="font-mono text-2xl font-bold tabular-nums"
      aria-live="polite"
    >
      {remaining}
    </span>
  );
}

interface ElapsedProps {
  startedAt: number;
}

export function Elapsed({ startedAt }: ElapsedProps): React.JSX.Element {
  const [now, setNow] = useState(() => performance.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(performance.now()), 500);
    return () => window.clearInterval(id);
  }, []);

  return <span className="font-mono tabular-nums">{Math.floor((now - startedAt) / 1000)}秒</span>;
}
