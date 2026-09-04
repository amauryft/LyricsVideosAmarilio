"""Drive ffmpeg to produce the final lyrics video."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .assgen import (
    SHOWCASE,
    build_ass,
    build_columns_ass,
    build_showcase_ass,
    showcase_block_metrics,
)
from .brand import Brand
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
    block_size: int = 1,
    brand: Brand | None = None,
    song_title: str | None = None,
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

    columns = brand is not None and brand.layout == "columns"
    showcase = brand is not None and brand.layout == "showcase"
    if showcase:
        waveform = True  # the live audio strip is part of this layout
    intro_end = 0.0
    if showcase:
        first_start = lyrics.lines[0].start
        if brand.intro and first_start >= 4.5:
            intro_end = min(first_start - 0.8, 8.0)
        ass_text = build_showcase_ass(
            lyrics, theme, brand, width, height, duration, intro_end,
            block_size=brand.lines or block_size or 4,
            song_title=song_title or title,
            author=artist or brand.artist,
        )
        if background is None:
            background = brand.background
    elif columns:
        ass_text = build_columns_ass(
            lyrics, theme, width, height, duration,
            block_size=brand.lines or block_size or 2,
            song_title=song_title or title or lyrics.title,
            credit=brand.credit,
            album=brand.album if not brand.cover else None,
            artist=artist or brand.artist,
            title_color=brand.title_color,
            credit_color=brand.credit_color,
        )
        if background is None:
            background = brand.background
    else:
        ass_text = build_ass(
            lyrics, theme, width, height,
            show_upcoming=show_upcoming, title=title, artist=artist,
            block_size=block_size,
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
        if columns and brand.bg_wash > 0:
            filters.append(
                f"color=c=white@{brand.bg_wash:.2f}:s={width}x{height}:r=30,"
                f"format=rgba[wash]"
            )
            filters.append(f"{base}[wash]overlay=shortest=1:format=auto[washed]")
            base = "[washed]"

        if columns and brand.cover:
            inputs += ["-loop", "1", "-framerate", "30", "-i", str(brand.cover)]
            cover_w = round(width * 0.15)
            filters.append(f"[2:v]scale={cover_w}:-1[cover]")
            filters.append(
                f"{base}[cover]overlay=x={round(width * 0.055)}:y={round(height * 0.105)}"
                f":format=auto[withcover]"
            )
            base = "[withcover]"

        if showcase and brand.cover:
            g = SHOWCASE
            inputs += ["-loop", "1", "-framerate", "30", "-i", str(brand.cover)]
            # Every cover gets a hard border to separate it from the art;
            # brands can pick the color, else the theme text color is used.
            border_color = brand.cover_border or theme.text_color
            b = max(2, round(width * 0.004))
            border = (
                f",pad=iw+{2 * b}:ih+{2 * b}:{b}:{b}"
                f":color=0x{border_color.lstrip('#')}"
            )
            small_w = round(width * g["cover_w"])
            small_x = round(width * g["cover_x"])
            small_y = round(height * g["cover_y"])
            if intro_end > 0:
                big_w = round(width * g["intro_cover_w"])
                big_x = round(width * g["intro_cover_x"])
                xfd = 0.35
                filters.append("[2:v]split[cbig0][csm0]")
                filters.append(
                    f"[cbig0]scale={big_w}:-1{border},format=rgba,"
                    f"fade=t=out:st={intro_end - xfd:.2f}:d={xfd}:alpha=1[cbig]"
                )
                filters.append(
                    f"[csm0]scale={small_w}:-1{border},format=rgba,"
                    f"fade=t=in:st={intro_end - xfd:.2f}:d={xfd}:alpha=1[csm]"
                )
                filters.append(f"{base}[cbig]overlay=x={big_x}:y=(H-h)/2:format=auto[wbig]")
                filters.append(f"[wbig][csm]overlay=x={small_x}:y={small_y}:format=auto[wcov]")
            else:
                filters.append(f"[2:v]scale={small_w}:-1{border}[csm]")
                filters.append(f"{base}[csm]overlay=x={small_x}:y={small_y}:format=auto[wcov]")
            base = "[wcov]"

            # Translucent title/author strip below the cover.
            bw = round(width * g["block_w"])
            _, strip_h, _ = showcase_block_metrics(
                song_title or title or lyrics.title or ""
            )
            bh = round(height * strip_h)
            strip_fade = (
                f",fade=t=in:st={max(0.0, intro_end - 0.2):.2f}:d=0.4:alpha=1"
                if intro_end > 0 else ""
            )
            filters.append(
                f"color=c=0x{brand.block_bg.lstrip('#')}@{brand.block_alpha:.2f}"
                f":s={bw}x{bh}:r=30,format=rgba{strip_fade}[strip]"
            )
            filters.append(
                f"{base}[strip]overlay=x={round(width * g['block_x'])}"
                f":y={round(height * g['block_y'])}:format=auto[wstrip]"
            )
            base = "[wstrip]"
        if waveform:
            wave_h = round(height * (0.14 if showcase else 0.18))
            # In the showcase layout the wave matches the highlighted lyric
            # color so the whole composition reads as one palette.
            wave_color = "0x" + (
                theme.text_color if showcase else theme.wave_color
            ).lstrip("#")
            wave_fade = (
                f",fade=t=in:st={intro_end:.2f}:d=0.6:alpha=1"
                if showcase and intro_end > 0 else ""
            )
            filters.append(
                f"[1:a]showwaves=s={width}x{wave_h}:mode=cline:rate=30"
                f":colors={wave_color}@0.55,format=rgba{wave_fade}[wave]"
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
