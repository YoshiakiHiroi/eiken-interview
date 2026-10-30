import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PRE2_GRADE } from "../../test/fixtures";
import type { Answer, Session } from "../types/api";
import { ScoreCard } from "./ScoreCard";

function answer(part: string, score: number | null): Answer {
  return {
    part,
    audio_url: "https://example.com/a.wav",
    follow_up_audio_url: null,
    duration_sec: 10,
    silence_before_sec: 1,
    replay_count: 0,
    yes_no: null,
    transcript: null,
    score,
    feedback_ja: null,
    model_answer: null,
    issue_tags: [],
    confidence: null,
    clarity: null,
    evaluation_error: null,
  };
}

function session(overrides: Partial<Session>): Session {
  return {
    id: "s1",
    uid: "u1",
    grade: "pre2",
    mode: "full",
    set_id: "pre2_dummy",
    started_at: "2026-10-30T00:00:00Z",
    finished_at: "2026-10-30T00:06:00Z",
    answers: [],
    attitude: null,
    total: null,
    passed: null,
    ...overrides,
  };
}

describe("ScoreCard", () => {
  it("shows the total out of the grade maximum and the pass judgement", () => {
    render(
      <ScoreCard
        grade={PRE2_GRADE}
        session={session({
          answers: [answer("read_aloud", 4), answer("q1", 5)],
          attitude: { score: 3, feedback_ja: "良い", evaluation_error: null },
          total: 27,
          passed: true,
        })}
      />,
    );
    expect(screen.getByText("27 / 33")).toBeDefined();
    expect(screen.getByText(/合格ライン到達/)).toBeDefined();
    expect(screen.getByText("4 / 5")).toBeDefined();
  });

  it("explains a missing total", () => {
    render(
      <ScoreCard
        grade={PRE2_GRADE}
        session={session({ answers: [answer("q1", null)] })}
      />,
    );
    expect(screen.getByText(/採点が終わっていないパートがあります/)).toBeDefined();
  });

  it("scores drills only over answered parts without a pass judgement", () => {
    render(
      <ScoreCard
        grade={PRE2_GRADE}
        session={session({ mode: "drill_q2", answers: [answer("q2", 3)], total: 3 })}
      />,
    );
    expect(screen.getAllByText("3 / 5")).toHaveLength(2);
    expect(screen.queryByText(/合格ライン/)).toBeNull();
  });
});
