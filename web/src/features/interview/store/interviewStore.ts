import { create } from "zustand";

import type { Answer, Grade, ProblemSet, Session } from "../../../shared/types/api";
import { buildInterviewSteps, type InterviewStep } from "../flow/interviewFlow";
import {
  createSession,
  fetchNextSet,
  finishSession,
  submitAnswer,
  type PartAnswer,
} from "../services/interviewApi";

export type SubmissionStatus = "sending" | "done" | "failed";

export interface Submission {
  status: SubmissionStatus;
  answer: PartAnswer;
  result: Answer | null;
  error: unknown;
}

type Phase = "idle" | "preparing" | "running" | "finishing" | "finished" | "error";

interface InterviewState {
  phase: Phase;
  grade: Grade | null;
  problemSet: ProblemSet | null;
  sessionId: string | null;
  steps: InterviewStep[];
  stepIndex: number;
  submissions: Record<string, Submission>;
  error: unknown;
  start: (grade: Grade) => Promise<void>;
  next: () => void;
  submit: (answer: PartAnswer) => Promise<void>;
  finish: () => Promise<Session | null>;
  reset: () => void;
}

const INITIAL = {
  phase: "idle" as Phase,
  grade: null,
  problemSet: null,
  sessionId: null,
  steps: [],
  stepIndex: 0,
  submissions: {},
  error: null,
};

export function hasPendingSubmissions(submissions: Record<string, Submission>): boolean {
  return Object.values(submissions).some((submission) => submission.status !== "done");
}

export const useInterviewStore = create<InterviewState>((set, get) => ({
  ...INITIAL,
  start: async (grade) => {
    set({ ...INITIAL, phase: "preparing", grade });
    try {
      const problemSet = await fetchNextSet(grade.grade, "full");
      const sessionId = await createSession("full", problemSet.id);
      set({ phase: "running", problemSet, sessionId, steps: buildInterviewSteps(grade) });
    } catch (error) {
      set({ phase: "error", error });
    }
  },
  next: () => {
    const { stepIndex, steps } = get();
    if (stepIndex + 1 < steps.length) {
      set({ stepIndex: stepIndex + 1 });
    } else {
      set({ phase: "finishing" });
    }
  },
  submit: async (answer) => {
    const sessionId = get().sessionId;
    if (!sessionId) {
      throw new Error("session has not started");
    }
    const update = (submission: Submission): void =>
      set((state) => ({ submissions: { ...state.submissions, [answer.partId]: submission } }));
    update({ status: "sending", answer, result: null, error: null });
    try {
      update({
        status: "done",
        answer,
        result: await submitAnswer(sessionId, answer),
        error: null,
      });
    } catch (error) {
      update({ status: "failed", answer, result: null, error });
    }
  },
  finish: async () => {
    const { sessionId, submissions } = get();
    if (!sessionId || hasPendingSubmissions(submissions)) {
      return null;
    }
    try {
      const session = await finishSession(sessionId);
      set({ phase: "finished" });
      return session;
    } catch (error) {
      set({ error });
      return null;
    }
  },
  reset: () => set(INITIAL),
}));
