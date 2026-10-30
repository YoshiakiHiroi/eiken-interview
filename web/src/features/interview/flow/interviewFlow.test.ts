import { describe, expect, it } from "vitest";

import { DUMMY_SET, PRE2_GRADE } from "../../../test/fixtures";
import {
  buildInterviewSteps,
  findQuestion,
  followUpPrompt,
  phrasePrompt,
  questionPrompt,
} from "./interviewFlow";

describe("buildInterviewSteps", () => {
  it("orders phrases, timers and answers from the grade config", () => {
    const steps = buildInterviewSteps(PRE2_GRADE).map((step) =>
      step.kind === "phrase"
        ? `phrase:${step.phraseKey}:${step.card}`
        : `${step.kind}:${step.part.id}`,
    );
    expect(steps).toEqual([
      "phrase:greeting:none",
      "phrase:silent_reading:passage",
      "timer:silent_reading",
      "phrase:read_aloud:passage",
      "answer:read_aloud",
      "phrase:five_questions:passage",
      "answer:q1",
      "answer:q2",
      "phrase:turn_over:none",
      "answer:q4",
      "phrase:end:none",
    ]);
  });

  it("uses the timer seconds from the grade config", () => {
    const timer = buildInterviewSteps(PRE2_GRADE).find((step) => step.kind === "timer");
    expect(timer?.kind === "timer" && timer.seconds).toBe(20);
  });
});

describe("prompts", () => {
  it("prefers pre-generated audio and falls back to the phrase text", () => {
    expect(phrasePrompt(PRE2_GRADE, DUMMY_SET, "greeting")).toEqual({
      url: "https://example.com/greeting.mp3",
      text: "Hello. May I have your card, please?",
    });
    expect(phrasePrompt(PRE2_GRADE, DUMMY_SET, "read_aloud")).toEqual({
      url: null,
      text: "Now, please read it aloud.",
    });
  });

  it("picks the follow-up question for the chosen answer", () => {
    const q4 = PRE2_GRADE.parts.find((part) => part.id === "q4");
    expect(q4).toBeDefined();
    const question = q4 ? findQuestion(DUMMY_SET, q4) : null;
    expect(questionPrompt(question)?.url).toBe("https://example.com/q4.mp3");
    expect(followUpPrompt(question, "yes")).toEqual({ url: null, text: "Why?" });
    expect(followUpPrompt(question, "no")).toEqual({
      url: "https://example.com/q4_no.mp3",
      text: "Why not?",
    });
  });

  it("has no question for parts without a question number", () => {
    const readAloud = PRE2_GRADE.parts.find((part) => part.id === "read_aloud");
    expect(readAloud && findQuestion(DUMMY_SET, readAloud)).toBeNull();
  });
});
