import { describe, expect, it } from "vitest";

import { fileExtensionFor, pickRecordingMimeType } from "./audio";

describe("pickRecordingMimeType", () => {
  it("prefers webm/opus when supported", () => {
    expect(pickRecordingMimeType(() => true)).toBe("audio/webm;codecs=opus");
  });

  it("falls back to mp4 on iOS Safari", () => {
    expect(pickRecordingMimeType((type) => type === "audio/mp4")).toBe("audio/mp4");
  });

  it("returns null when nothing is supported", () => {
    expect(pickRecordingMimeType(() => false)).toBeNull();
  });
});

describe("fileExtensionFor", () => {
  it.each([
    ["audio/webm;codecs=opus", "webm"],
    ["audio/mp4", "mp4"],
    ["audio/ogg;codecs=opus", "ogg"],
  ])("%s -> %s", (mimeType, extension) => {
    expect(fileExtensionFor(mimeType)).toBe(extension);
  });
});
