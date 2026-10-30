import { describe, expect, it, vi } from "vitest";

vi.mock("../../../shared/lib/apiClient", () => ({ apiRequest: vi.fn(), postJson: vi.fn() }));

import type { Recording } from "../../../shared/hooks/useRecorder";
import { buildAnswerForm } from "./interviewApi";

function recording(mimeType: string): Recording {
  return {
    blob: new Blob(["x"], { type: mimeType }),
    mimeType,
    durationSec: 12.345,
    silenceBeforeSec: 1.5,
  };
}

describe("buildAnswerForm", () => {
  it("sends the main recording with timing metadata", () => {
    const form = buildAnswerForm({
      partId: "q2",
      main: recording("audio/mp4"),
      followUp: null,
      yesNo: null,
      replayCount: 1,
    });
    expect((form.get("audio") as File).name).toBe("answer.mp4");
    expect(form.get("duration_sec")).toBe("12.35");
    expect(form.get("silence_before_sec")).toBe("1.50");
    expect(form.get("replay_count")).toBe("1");
    expect(form.has("yes_no")).toBe(false);
    expect(form.has("follow_up_audio")).toBe(false);
  });

  it("adds yes/no and the follow-up recording", () => {
    const form = buildAnswerForm({
      partId: "q4",
      main: recording("audio/webm;codecs=opus"),
      followUp: recording("audio/webm;codecs=opus"),
      yesNo: "no",
      replayCount: 0,
    });
    expect(form.get("yes_no")).toBe("no");
    expect((form.get("follow_up_audio") as File).name).toBe("follow_up.webm");
  });
});
