#!/usr/bin/env python3
"""Place official lyric lines onto transcription timing anchors.

The per-song workflow (README) is: keep the raw transcription as timing
anchors, then write the final .lrc with the official PDF lines on those
anchors — and where whisper merged several sung lines into one segment,
space the official lines evenly across that segment's span. Doing that by
hand is arithmetic-heavy and easy to get subtly wrong across a whole
album, so this does the spacing.

Input is a plain-text spec:

    # comments and blank lines are ignored
    @0:30.80 - 0:45.88          <- segment: spread the lines below over it
    Ele voltará
    Indubitavelmente, sim, Ele voltará

    @1:45.28 .                  <- a lone '.' marks an instrumental break
    @2:18.26 - 2:32.92
    Sem guizos nem amarras,

A segment's end is exclusive: the last line runs up to it. Ends may be
omitted (`@1:20.95`) when the next segment's start should bound it.

Usage:
    python3 tools/fit_lrc.py spec.txt -o songs/<slug>.lrc \
        --title "Título" --artist "Amarilio Fontenele"
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SEG = re.compile(r"^@\s*([0-9:.]+)\s*(?:[-–]\s*([0-9:.]+)\s*)?(\.)?\s*$")


def parse_time(text: str) -> float:
    """'1:16.85', '76.85' and '0:01:16.85' all mean 76.85 seconds."""
    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(f"bad timestamp: {text}")
    total = 0.0
    for part in parts:
        total = total * 60 + float(part)
    return total


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    return f"[{int(seconds // 60):02d}:{seconds % 60:05.2f}]"


def parse_spec(text: str) -> list[tuple[float, float | None, list[str], bool]]:
    segments: list[tuple[float, float | None, list[str], bool]] = []
    start = end = None
    is_break = False
    lines: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = SEG.match(line)
        if m:
            if start is not None:
                segments.append((start, end, lines, is_break))
            start = parse_time(m.group(1))
            end = parse_time(m.group(2)) if m.group(2) else None
            is_break = bool(m.group(3))
            lines = []
        else:
            if start is None:
                raise ValueError(f"lyric line before any @segment: {line!r}")
            lines.append(line)
    if start is not None:
        segments.append((start, end, lines, is_break))
    return segments


def build(segments, title, artist) -> str:
    out = []
    if title:
        out.append(f"[ti:{title}]")
    if artist:
        out.append(f"[ar:{artist}]")
    out.append("")

    for i, (start, end, lines, is_break) in enumerate(segments):
        if is_break or not lines:
            out.append(fmt_time(start))
            continue
        stop = end
        if stop is None:
            stop = segments[i + 1][0] if i + 1 < len(segments) else start + len(lines) * 3.5
        if stop <= start:
            raise ValueError(f"segment at {start} ends at or before it starts")
        step = (stop - start) / len(lines)
        for j, line in enumerate(lines):
            out.append(f"{fmt_time(start + j * step)}{line}")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="Spec file (see module docstring)")
    ap.add_argument("-o", "--output", required=True, help="Output .lrc path")
    ap.add_argument("--title", default=None)
    ap.add_argument("--artist", default="Amarilio Fontenele")
    args = ap.parse_args(argv)

    try:
        segments = parse_spec(Path(args.spec).read_text(encoding="utf-8"))
        lrc = build(segments, args.title, args.artist)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    Path(args.output).write_text(lrc, encoding="utf-8")
    sung = sum(1 for ln in lrc.splitlines() if ln.startswith("[0") and ln[10:].strip())
    print(f"wrote {args.output} ({sung} lyric lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
