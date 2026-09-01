"""Command line interface: `lyricsvideo` (or `python -m lyricsvideo`)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import __version__
from .render import RenderError, render_video
from .themes import DEFAULT_THEME, THEMES, get_theme


def _parse_resolution(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{2,5})x(\d{2,5})", value)
    if not match:
        raise argparse.ArgumentTypeError(
            f"Invalid resolution {value!r}; expected WIDTHxHEIGHT, e.g. 1920x1080"
        )
    w, h = int(match.group(1)), int(match.group(2))
    # libx264 with yuv420p needs even dimensions.
    return w - w % 2, h - h % 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lyricsvideo",
        description="Render a lyrics video from an audio file and a timed .lrc lyrics file.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    render = sub.add_parser("render", help="Render a lyrics video")
    render.add_argument("audio", type=Path, help="Audio file (mp3, wav, flac, m4a, ...)")
    render.add_argument("lyrics", type=Path, help="Timed lyrics file (.lrc)")
    render.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output mp4 path (default: output/<audio-stem>.mp4)",
    )
    render.add_argument(
        "-t", "--theme", default=DEFAULT_THEME, choices=sorted(THEMES),
        help=f"Visual theme (default: {DEFAULT_THEME})",
    )
    render.add_argument(
        "-b", "--background", type=Path, default=None,
        help="Background image or video (replaces the theme gradient)",
    )
    render.add_argument(
        "-r", "--resolution", type=_parse_resolution, default=(1920, 1080),
        metavar="WxH", help="Output resolution (default: 1920x1080; use 1080x1920 for shorts)",
    )
    render.add_argument(
        "-w", "--waveform", action="store_true",
        help="Overlay an audio waveform near the bottom of the frame",
    )
    render.add_argument(
        "--no-upcoming", action="store_true",
        help="Hide the dimmed preview of the next lyric line",
    )
    render.add_argument(
        "-n", "--lines", type=int, default=1, metavar="N",
        help="Show N lyric lines at a time as a stanza, highlighting the "
             "current one (default: 1 = single-line mode)",
    )
    render.add_argument("--title", help="Song title for the intro card (overrides [ti:] tag)")
    render.add_argument("--artist", help="Artist for the intro card (overrides [ar:] tag)")
    render.add_argument(
        "--brand", type=Path, default=None, metavar="JSON",
        help="Brand config JSON (layout, colors, fonts, cover, background)",
    )
    render.add_argument(
        "--song-title", default=None,
        help="Song title text for the columns layout (default: [ti:] tag)",
    )
    render.add_argument(
        "-p", "--preview", type=float, metavar="SECONDS", default=None,
        help="Render only the first N seconds (fast iteration)",
    )
    render.add_argument("-q", "--quiet", action="store_true", help="Suppress ffmpeg output")

    themes = sub.add_parser("themes", help="List available themes")
    themes.set_defaults(command="themes")

    tr = sub.add_parser(
        "transcribe",
        help="Transcribe sung lyrics from audio into a timed .lrc (needs faster-whisper)",
    )
    tr.add_argument("audio", type=Path, help="Audio file to transcribe")
    tr.add_argument(
        "-o", "--output", type=Path, default=None,
        help="Output .lrc path (default: <audio-stem>.lrc next to the audio)",
    )
    tr.add_argument(
        "-l", "--language", default=None,
        help="ISO language code, e.g. pt, en, es (default: auto-detect)",
    )
    tr.add_argument(
        "-m", "--model", default="medium",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        help="Whisper model size; bigger = more accurate but slower (default: medium)",
    )
    tr.add_argument("--title", help="Song title written to the [ti:] tag")
    tr.add_argument("--artist", help="Artist written to the [ar:] tag")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "themes":
        width = max(len(name) for name in THEMES)
        for name in sorted(THEMES):
            theme = THEMES[name]
            marker = "*" if name == DEFAULT_THEME else " "
            print(f"{marker} {name:<{width}}  {theme.description}")
        print("\n* default")
        return 0

    if args.command == "transcribe":
        if not args.audio.is_file():
            print(f"error: Audio file not found: {args.audio}", file=sys.stderr)
            return 2
        from .transcribe import TranscribeError, transcribe_to_lrc

        output = args.output or args.audio.with_suffix(".lrc")
        try:
            result = transcribe_to_lrc(
                audio=args.audio,
                output=output,
                language=args.language,
                model_size=args.model,
                title=args.title,
                artist=args.artist,
            )
        except TranscribeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"Wrote: {result}")
        print("Review the words and timings before rendering — sung-vocal "
              "transcription is rarely perfect.")
        return 0

    for path, label in ((args.audio, "Audio"), (args.lyrics, "Lyrics")):
        if not path.is_file():
            print(f"error: {label} file not found: {path}", file=sys.stderr)
            return 2
    if args.background and not args.background.is_file():
        print(f"error: Background file not found: {args.background}", file=sys.stderr)
        return 2

    output = args.output or Path("output") / f"{args.audio.stem}.mp4"
    width, height = args.resolution

    brand = None
    theme = get_theme(args.theme)
    if args.brand:
        from .brand import load_brand

        try:
            brand = load_brand(args.brand)
        except (OSError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        theme = brand.apply_to(theme)

    try:
        result = render_video(
            audio=args.audio,
            lyrics_path=args.lyrics,
            output=output,
            theme=theme,
            width=width,
            height=height,
            background=args.background,
            waveform=args.waveform,
            show_upcoming=not args.no_upcoming,
            title=args.title,
            artist=args.artist,
            block_size=max(1, args.lines),
            brand=brand,
            song_title=args.song_title,
            preview_seconds=args.preview,
            quiet=args.quiet,
        )
    except RenderError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Rendered: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
