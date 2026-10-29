import io
import wave

import pytest

from eiken_api.services.audio import SAMPLE_RATE, AudioConversionError, to_wav


@pytest.mark.parametrize("ext", ["webm", "ogg", "mp4"])
def test_to_wav_converts_browser_formats_to_16k_mono(audio_samples: dict[str, bytes], ext: str) -> None:
    with wave.open(io.BytesIO(to_wav(audio_samples[ext]))) as wav:
        assert wav.getnchannels() == 1
        assert wav.getframerate() == SAMPLE_RATE
        assert wav.getnframes() / SAMPLE_RATE == pytest.approx(1.0, abs=0.1)


@pytest.mark.parametrize("data", [b"", b"not audio at all"])
def test_to_wav_rejects_invalid_input(data: bytes) -> None:
    with pytest.raises(AudioConversionError):
        to_wav(data)
