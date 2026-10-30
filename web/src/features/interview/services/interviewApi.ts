import { fileExtensionFor } from "../../../shared/lib/audio";
import { apiRequest, postJson } from "../../../shared/lib/apiClient";
import type { Recording } from "../../../shared/hooks/useRecorder";
import type { Answer, ProblemSet, Session, SessionMode, YesNo } from "../../../shared/types/api";

export interface PartAnswer {
  partId: string;
  main: Recording;
  followUp: Recording | null;
  yesNo: YesNo | null;
  replayCount: number;
}

export function fetchNextSet(grade: string, mode: SessionMode): Promise<ProblemSet> {
  const query = new URLSearchParams({ grade, mode });
  return apiRequest<ProblemSet>(`/api/sets/next?${query.toString()}`);
}

export function fetchSet(setId: string): Promise<ProblemSet> {
  return apiRequest<ProblemSet>(`/api/sets/${encodeURIComponent(setId)}`);
}

export async function createSession(mode: SessionMode, setId: string): Promise<string> {
  const { session_id: sessionId } = await postJson<{ session_id: string }>("/api/sessions", {
    mode,
    set_id: setId,
  });
  return sessionId;
}

export function fetchSession(sessionId: string): Promise<Session> {
  return apiRequest<Session>(`/api/sessions/${encodeURIComponent(sessionId)}`);
}

export function buildAnswerForm(answer: PartAnswer): FormData {
  const form = new FormData();
  form.append("audio", answer.main.blob, `answer.${fileExtensionFor(answer.main.mimeType)}`);
  form.append("duration_sec", answer.main.durationSec.toFixed(2));
  form.append("silence_before_sec", answer.main.silenceBeforeSec.toFixed(2));
  form.append("replay_count", String(answer.replayCount));
  if (answer.yesNo) {
    form.append("yes_no", answer.yesNo);
  }
  if (answer.followUp) {
    form.append(
      "follow_up_audio",
      answer.followUp.blob,
      `follow_up.${fileExtensionFor(answer.followUp.mimeType)}`,
    );
  }
  return form;
}

export function submitAnswer(sessionId: string, answer: PartAnswer): Promise<Answer> {
  return apiRequest<Answer>(
    `/api/sessions/${encodeURIComponent(sessionId)}/answers/${encodeURIComponent(answer.partId)}`,
    { method: "POST", body: buildAnswerForm(answer) },
  );
}

export function finishSession(sessionId: string): Promise<Session> {
  return apiRequest<Session>(`/api/sessions/${encodeURIComponent(sessionId)}/finish`, {
    method: "POST",
  });
}
