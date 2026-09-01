"""Transcribe sung lyrics from audio into a timed .lrc file using Whisper.

Requires the optional dependency: pip install faster-whisper
"""

from __future__ import annotations

from pathlib import Path


class TranscribeError(RuntimeError):
    pass


def _format_tag(seconds: float) -> str:
    seconds = max(0.0, seconds)
    m = int(seconds // 60)
    s = seconds % 60
    return f"[{m:02d}:{s:05.2f}]"


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
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise TranscribeError(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from None

    audio = audio.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

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

    lines: list[str] = []
    if title:
        lines.append(f"[ti:{title}]")
    if artist:
        lines.append(f"[ar:{artist}]")
    lines.append("")

    last_end = 0.0
    for seg in segments:
        text = seg.text.strip()
        if not text:
            continue
        # Mark instrumental gaps so the previous line leaves the screen.
        if last_end and seg.start - last_end > 4.0:
            lines.append(_format_tag(last_end + 0.5))
        lines.append(f"{_format_tag(seg.start)}{text}")
        last_end = seg.end
        if progress:
            print(f"  {_format_tag(seg.start)} {text}", flush=True)

    if last_end:
        lines.append(_format_tag(last_end + 0.5))

    if len(lines) <= 3:
        raise TranscribeError(f"No speech/singing detected in {audio}")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if progress:
        print(f"Detected language: {info.language} (p={info.language_probability:.2f})")
    return output
