"""Generate sample answer recordings with Cloud Text-to-Speech for manual API checks.

The audio is encoded as webm/opus, the same format browsers send from MediaRecorder.

Usage: cd api && uv run python ../scripts/generate_fixtures.py --voice en-US-Chirp3-HD-Puck
"""

import argparse
import subprocess
import tempfile
from pathlib import Path

from google.cloud import texttospeech

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "api" / "tests" / "fixtures"

# 準2級ダミーセット（scripts/seed_dummy_set.py）に対する回答
ANSWERS = {
    "read_aloud": (
        "Many people today are interested in protecting the environment. Some families sort their garbage "
        "carefully at home, and by doing so, they can help reduce waste. Recycling is becoming a part of daily life."
    ),
    "q1": "By sorting their garbage carefully at home.",
    "q2": "A man is carrying a box. A woman is watering flowers. A boy is riding a bicycle. A girl feed a dog.",
    "q3": "She wants to open the door, but she can't because her hands are full.",
    "q4_first": "Yes, I do.",
    "q4_follow_up": "Recycling is becoming easier. Many supermarkets have recycling boxes.",
    "q5_first": "No, I don't.",
    "q5_follow_up": "I am very busy.",
}


def synthesize_wav(client: texttospeech.TextToSpeechClient, text: str, voice: str) -> bytes:
    response = client.synthesize_speech(
        input=texttospeech.SynthesisInput(text=text),
        voice=texttospeech.VoiceSelectionParams(language_code=voice[:5], name=voice),
        audio_config=texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.LINEAR16),
    )
    return response.audio_content


def wav_to_webm(wav: bytes, target: Path) -> None:
    with tempfile.NamedTemporaryFile(suffix=".wav") as source:
        source.write(wav)
        source.flush()
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", source.name, "-c:a", "libopus", str(target)],
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", required=True)
    args = parser.parse_args()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    client = texttospeech.TextToSpeechClient()
    for name, text in ANSWERS.items():
        target = FIXTURES_DIR / f"{name}.webm"
        wav_to_webm(synthesize_wav(client, text, args.voice), target)
        print(f"wrote {target.relative_to(FIXTURES_DIR.parent.parent.parent)}")


if __name__ == "__main__":
    main()
