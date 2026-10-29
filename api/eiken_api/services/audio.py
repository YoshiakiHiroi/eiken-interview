import subprocess
import tempfile
from pathlib import Path

SAMPLE_RATE = 16000
CONVERT_TIMEOUT_SEC = 30


class AudioConversionError(Exception):
    pass


def ffmpeg_to_wav_args(input_path: str, output_path: str, sample_rate: int = SAMPLE_RATE) -> list[str]:
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        input_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "wav",
        output_path,
    ]


def to_wav(data: bytes) -> bytes:
    """Convert webm / mp4 / ogg audio to 16 kHz mono WAV."""
    if not data:
        raise AudioConversionError("empty audio")
    # 入出力ともファイルにする。入力: iOS Safari の mp4 は moov atom が末尾にありパイプではシークできない。
    # 出力: パイプだと WAV ヘッダのデータ長を書き戻せず不正な長さになる。
    with tempfile.TemporaryDirectory() as workdir:
        source = Path(workdir) / "input"
        target = Path(workdir) / "output.wav"
        source.write_bytes(data)
        try:
            result = subprocess.run(
                ffmpeg_to_wav_args(str(source), str(target)),
                capture_output=True,
                timeout=CONVERT_TIMEOUT_SEC,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AudioConversionError("ffmpeg timed out") from exc
        if result.returncode != 0 or not target.is_file() or target.stat().st_size == 0:
            raise AudioConversionError(result.stderr.decode(errors="replace").strip() or "ffmpeg failed")
        return target.read_bytes()
