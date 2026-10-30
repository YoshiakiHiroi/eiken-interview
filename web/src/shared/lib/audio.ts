const RECORDING_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
];
const SPEECH_RATE = 0.95;

export interface Prompt {
  url: string | null;
  text: string;
}

export function pickRecordingMimeType(isSupported: (mimeType: string) => boolean): string | null {
  return RECORDING_MIME_TYPES.find((mimeType) => isSupported(mimeType)) ?? null;
}

export function fileExtensionFor(mimeType: string): string {
  if (mimeType.startsWith("audio/mp4")) {
    return "mp4";
  }
  if (mimeType.startsWith("audio/ogg")) {
    return "ogg";
  }
  return "webm";
}

let currentAudio: HTMLAudioElement | null = null;

export function stopPlayback(): void {
  currentAudio?.pause();
  currentAudio = null;
  window.speechSynthesis.cancel();
}

function playUrl(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const audio = new Audio(url);
    currentAudio = audio;
    audio.onended = () => resolve();
    audio.onerror = () => reject(new Error(`音声を再生できませんでした: ${url}`));
    audio.play().catch(reject);
  });
}

// 事前生成の TTS 音声がないセット（ダミーセットなど）では、ブラウザの読み上げで代替する
function speak(text: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-US";
    utterance.rate = SPEECH_RATE;
    utterance.onend = () => resolve();
    utterance.onerror = (event) => reject(new Error(`読み上げに失敗しました: ${event.error}`));
    window.speechSynthesis.speak(utterance);
  });
}

export async function playPrompt(prompt: Prompt): Promise<void> {
  stopPlayback();
  if (prompt.url) {
    await playUrl(prompt.url);
    return;
  }
  if (prompt.text) {
    await speak(prompt.text);
  }
}
