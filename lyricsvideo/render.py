"""Drive ffmpeg to produce the final lyrics video."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .assgen import build_ass
from .lrc import load_lrc
from .themes import Theme


class RenderError(RuntimeError):
    pass


def _require(binary: str) -> str:
    path = shutil.which(binary)
    if not path:
        raise RenderError(
            f"{binary} not found on PATH. Install ffmpeg (e.g. `apt install ffmpeg` "
            "or `brew install ffmpeg`) and try again."
        )
    return path


def probe_duration(audio: Path) -> float:
    ffprobe = _require("ffprobe")
    out = subprocess.run(
        [
            ffprobe, "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(audio),
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    try:
        return float(json.loads(out)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as exc:
        raise RenderError(f"Could not read duration of {audio}: {out}") from exc


def _ffmpeg_gradient(theme: Theme, width: int, height: int, duration: float) -> str:
    c0 = "0x" + theme.bg_top.lstrip("#")
    c1 = "0x" + theme.bg_bottom.lstrip("#")
    # speed keeps the gradient drifting very slowly so the background feels alive.
    return (
        f"gradients=s={width}x{height}:c0={c0}:c1={c1}"
        f":x0={width // 2}:y0=0:x1={width // 2}:y1={height}"
        f":d={duration:.3f}:speed=0.012:r=30"
    )


def render_video(
    audio: Path,
    lyrics_path: Path,
    output: Path,
    theme: Theme,
    width: int = 1920,
    height: int = 1080,
    background: Path | None = None,
    waveform: bool = False,
    show_upcoming: bool = True,
    title: str | None = None,
    artist: str | None = None,
    preview_seconds: float | None = None,
    quiet: bool = False,
) -> Path:
    """Render the lyrics video and return the output path."""
    ffmpeg = _require("ffmpeg")
    audio = audio.resolve()
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    duration = probe_duration(audio)
    if preview_seconds:
        duration = min(duration, preview_seconds)

    lyrics = load_lrc(lyrics_path, audio_duration=duration)
    if not lyrics.lines:
        raise RenderError(f"No timed lyric lines found in {lyrics_path}")

    ass_text = build_ass(
        lyrics, theme, width, height,
        show_upcoming=show_upcoming, title=title, artist=artist,
    )

    with tempfile.TemporaryDirectory(prefix="lyricsvideo-") as tmp:
        ass_file = Path(tmp) / "lyrics.ass"
        ass_file.write_text(ass_text, encoding="utf-8")

        inputs: list[str] = []
        filters: list[str] = []

        if background:
            background = background.resolve()
            is_image = background.suffix.lower() in {
                ".png", ".jpg", ".jpeg", ".webp", ".bmp",
            }
            if is_image:
                inputs += ["-loop", "1", "-framerate", "30", "-i", str(background)]
            else:
                inputs += ["-stream_loop", "-1", "-i", str(background)]
            filters.append(
                f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
                f"crop={width}:{height},setsar=1,fps=30[bg]"
            )
        else:
            inputs += ["-f", "lavfi", "-i", _ffmpeg_gradient(theme, width, height, duration)]
            filters.append("[0:v]setsar=1[bg]")

        inputs += ["-i", str(audio)]

        base = "[bg]"
        if waveform:
            wave_h = round(height * 0.18)
            wave_color = "0x" + theme.wave_color.lstrip("#")
            filters.append(
                f"[1:a]showwaves=s={width}x{wave_h}:mode=cline:rate=30"
                f":colors={wave_color}@0.55,format=rgba[wave]"
            )
            filters.append(
                f"{base}[wave]overlay=x=0:y={height - wave_h - round(height * 0.04)}"
                ":format=auto[withwave]"
            )
            base = "[withwave]"

        # Burn the lyrics last so they sit on top of everything.
        filters.append(f"{base}ass=filename={ass_file.name}[out]")

        cmd = [
            ffmpeg, "-y", "-hide_banner",
            *(["-loglevel", "error"] if quiet else []),
            *inputs,
            "-filter_complex", ";".join(filters),
            "-map", "[out]", "-map", "1:a",
            "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output),
        ]

        # Run from the temp dir so the ass filter sees a plain filename and no
        # path-escaping is needed.
        result = subprocess.run(cmd, cwd=tmp, capture_output=quiet, text=True)
        if result.returncode != 0:
            detail = (result.stderr or "").strip()[-2000:] if quiet else ""
            raise RenderError(f"ffmpeg failed (exit {result.returncode}). {detail}")

    return output
