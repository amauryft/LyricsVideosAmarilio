"""Transcribe sung lyrics from audio into a timed .lrc file using Whisper.

Two interchangeable backends:

- faster-whisper (pip install faster-whisper): models auto-download from
  Hugging Face.
- sherpa-onnx (pip install sherpa-onnx numpy): fully offline, using a
  Whisper ONNX model directory + silero VAD file downloaded once from the
  sherpa-onnx GitHub releases. Used automatically when the env var
  LYRICSVIDEO_SHERPA_MODELS points at a directory containing
  sherpa-onnx-whisper-<name>/ and silero_vad.onnx, or when faster-whisper
  is unavailable/cannot reach its model host.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


class TranscribeError(RuntimeError):
    pass


def _format_tag(seconds: float) -> str:
    seconds = max(0.0, seconds)
    m = int(seconds // 60)
    s = seconds % 60
    return f"[{m:02d}:{s:05.2f}]"


def _write_lrc(
    output: Path,
    segments: list[tuple[float, float, str]],
    title: str | None,
    artist: str | None,
) -> None:
    """segments: (start, end, text), sorted by start."""
    lines: list[str] = []
    if title:
        lines.append(f"[ti:{title}]")
    if artist:
        lines.append(f"[ar:{artist}]")
    lines.append("")

    last_end = 0.0
    for start, end, text in segments:
        # Mark instrumental gaps so the previous line leaves the screen.
        if last_end and start - last_end > 4.0:
            lines.append(_format_tag(last_end + 0.5))
        lines.append(f"{_format_tag(start)}{text}")
        last_end = end
    if last_end:
        lines.append(_format_tag(last_end + 0.5))

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _sherpa_models_dir() -> Path | None:
    env = os.environ.get("LYRICSVIDEO_SHERPA_MODELS")
    for candidate in ([Path(env)] if env else []) + [Path("/home/user/models")]:
        if candidate.is_dir() and (candidate / "silero_vad.onnx").is_file():
            if any(candidate.glob("sherpa-onnx-whisper-*/")):
                return candidate
    return None


def _transcribe_sherpa(
    audio: Path, language: str | None, models_dir: Path, progress: bool
) -> list[tuple[float, float, str]]:
    """Offline backend: silero VAD chunking + Whisper ONNX via sherpa-onnx."""
    try:
        import numpy as np
        import sherpa_onnx
    except ImportError:
        raise TranscribeError(
            "sherpa-onnx backend needs: pip install sherpa-onnx numpy"
        ) from None

    whisper_dir = sorted(models_dir.glob("sherpa-onnx-whisper-*/"))[-1]
    stem = whisper_dir.name.removeprefix("sherpa-onnx-whisper-")

    def pick(part: str) -> str:
        int8 = whisper_dir / f"{stem}-{part}.int8.onnx"
        return str(int8 if int8.exists() else whisper_dir / f"{stem}-{part}.onnx")

    with tempfile.TemporaryDirectory(prefix="lyricsvideo-asr-") as tmp:
        wav = Path(tmp) / "audio16k.wav"
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise TranscribeError("ffmpeg not found on PATH (needed to decode audio)")
        subprocess.run(
            [ffmpeg, "-y", "-v", "error", "-i", str(audio),
             "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(wav)],
            check=True,
        )
        import wave

        with wave.open(str(wav)) as f:
            data = f.readframes(f.getnframes())
        samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

    vad_config = sherpa_onnx.VadModelConfig()
    vad_config.silero_vad.model = str(models_dir / "silero_vad.onnx")
    vad_config.silero_vad.threshold = 0.5
    vad_config.silero_vad.min_silence_duration = 0.6
    vad_config.silero_vad.min_speech_duration = 0.3
    vad_config.silero_vad.max_speech_duration = 28.0  # whisper window headroom
    vad_config.sample_rate = 16000
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=600)

    recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=pick("encoder"),
        decoder=pick("decoder"),
        tokens=str(whisper_dir / f"{stem}-tokens.txt"),
        language=language or "",
        task="transcribe",
        num_threads=max(1, os.cpu_count() or 1),
    )

    chunks: list[tuple[float, "np.ndarray"]] = []
    window = 512
    for i in range(0, len(samples), window):
        vad.accept_waveform(samples[i:i + window])
        while not vad.empty():
            seg = vad.front
            chunks.append((seg.start / 16000.0, np.asarray(seg.samples, dtype=np.float32)))
            vad.pop()
    vad.flush()
    while not vad.empty():
        seg = vad.front
        chunks.append((seg.start / 16000.0, np.asarray(seg.samples, dtype=np.float32)))
        vad.pop()

    segments: list[tuple[float, float, str]] = []
    for start, chunk in chunks:
        stream = recognizer.create_stream()
        stream.accept_waveform(16000, chunk)
        recognizer.decode_stream(stream)
        text = stream.result.text.strip()
        if not text:
            continue
        end = start + len(chunk) / 16000.0
        segments.append((start, end, text))
        if progress:
            print(f"  {_format_tag(start)} {text}", flush=True)
    return segments


def transcribe_to_lrc(
    audio: Path,
    output: Path,
    language: str | None = None,
    model_size: str = "medium",
    title: str | None = None,
    artist: str | None = None,
    progress: bool = True,
) -> Path:
    """Run Whisper on the audio and write an LRC file with one line per segment."""
    audio = audio.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    sherpa_dir = _sherpa_models_dir()
    if sherpa_dir is not None:
        segments = _transcribe_sherpa(audio, language, sherpa_dir, progress)
        if not segments:
            raise TranscribeError(f"No speech/singing detected in {audio}")
        _write_lrc(output, segments, title, artist)
        if progress:
            print(f"Backend: sherpa-onnx ({sherpa_dir})")
        return output

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscribeError(
            "No transcription backend available. Either `pip install "
            "faster-whisper` (downloads models from Hugging Face) or install "
            "sherpa-onnx models and set LYRICSVIDEO_SHERPA_MODELS (see README)."
        ) from None

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(audio),
        language=language,
        vad_filter=True,
        # Sung vocals repeat a lot; letting the decoder condition on previous
        # text makes it get stuck in loops, so turn that off.
        condition_on_previous_text=False,
        beam_size=5,
    )

    collected: list[tuple[float, float, str]] = []
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        collected.append((seg.start, seg.end, text))
        if progress:
            print(f"  {_format_tag(seg.start)} {text}", flush=True)

    if not collected:
        raise TranscribeError(f"No speech/singing detected in {audio}")

    _write_lrc(output, collected, title, artist)
    if progress:
        print(f"Detected language: {info.language} (p={info.language_probability:.2f})")
    return output
