import { useCallback, useEffect, useRef, useState } from "react";

import { pickRecordingMimeType } from "../lib/audio";

const VOICE_RMS_THRESHOLD = 0.02;

export interface Recording {
  blob: Blob;
  mimeType: string;
  durationSec: number;
  silenceBeforeSec: number;
}

export type RecorderStatus = "idle" | "recording" | "error";

interface RecorderHandle {
  status: RecorderStatus;
  error: string | null;
  start: () => Promise<void>;
  stop: () => Promise<Recording>;
}

function rootMeanSquare(samples: Float32Array): number {
  const sum = samples.reduce((total, sample) => total + sample * sample, 0);
  return Math.sqrt(sum / samples.length);
}

function describeMicError(error: unknown): string {
  if (error instanceof DOMException && error.name === "NotAllowedError") {
    return "マイクの使用が許可されていません。ブラウザの設定でマイクを許可してください。";
  }
  if (error instanceof DOMException && error.name === "NotFoundError") {
    return "マイクが見つかりません。";
  }
  return error instanceof Error ? error.message : String(error);
}

export function useRecorder(): RecorderHandle {
  const [status, setStatus] = useState<RecorderStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const startedAtRef = useRef(0);
  const voiceAtRef = useRef<number | null>(null);
  const frameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  const stopMonitoring = useCallback((): void => {
    if (frameRef.current !== null) {
      cancelAnimationFrame(frameRef.current);
      frameRef.current = null;
    }
    void audioContextRef.current?.close();
    audioContextRef.current = null;
  }, []);

  const releaseStream = useCallback((): void => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      stopMonitoring();
      releaseStream();
    };
  }, [releaseStream, stopMonitoring]);

  const start = useCallback(async (): Promise<void> => {
    if (typeof MediaRecorder === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      setStatus("error");
      setError(
        "このブラウザは録音に対応していません。最新の Chrome または Safari を使ってください。",
      );
      return;
    }
    const mimeType = pickRecordingMimeType((type) => MediaRecorder.isTypeSupported(type));
    if (!mimeType) {
      setStatus("error");
      setError("対応している録音形式がありません。");
      return;
    }
    try {
      streamRef.current ??= await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (micError) {
      setStatus("error");
      setError(describeMicError(micError));
      return;
    }

    const stream = streamRef.current;
    const recorder = new MediaRecorder(stream, { mimeType });
    chunksRef.current = [];
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    const audioContext = new AudioContext();
    const analyser = audioContext.createAnalyser();
    audioContext.createMediaStreamSource(stream).connect(analyser);
    const samples = new Float32Array(analyser.fftSize);
    audioContextRef.current = audioContext;
    voiceAtRef.current = null;

    const monitor = (): void => {
      analyser.getFloatTimeDomainData(samples);
      if (voiceAtRef.current === null && rootMeanSquare(samples) > VOICE_RMS_THRESHOLD) {
        voiceAtRef.current = performance.now();
      }
      frameRef.current = requestAnimationFrame(monitor);
    };

    recorderRef.current = recorder;
    startedAtRef.current = performance.now();
    recorder.start();
    monitor();
    setError(null);
    setStatus("recording");
  }, []);

  const stop = useCallback((): Promise<Recording> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      return Promise.reject(new Error("録音していません"));
    }
    return new Promise((resolve) => {
      recorder.onstop = () => {
        const stoppedAt = performance.now();
        stopMonitoring();
        const voiceAt = voiceAtRef.current ?? stoppedAt;
        setStatus("idle");
        resolve({
          blob: new Blob(chunksRef.current, { type: recorder.mimeType }),
          mimeType: recorder.mimeType,
          durationSec: (stoppedAt - startedAtRef.current) / 1000,
          silenceBeforeSec: (voiceAt - startedAtRef.current) / 1000,
        });
      };
      recorder.stop();
    });
  }, [stopMonitoring]);

  return { status, error, start, stop };
}
