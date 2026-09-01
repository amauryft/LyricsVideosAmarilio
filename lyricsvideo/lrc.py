"""Parsing of timed lyrics files (.lrc)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

TIME_TAG = re.compile(r"\[(\d+):(\d{1,2})(?:[.:](\d{1,3}))?\]")
META_TAG = re.compile(r"^\[(ti|ar|al|by|offset):\s*(.*?)\s*\]$", re.IGNORECASE)

# How long the last lyric line stays on screen when nothing follows it.
DEFAULT_LAST_LINE_HOLD = 5.0


@dataclass
class LyricLine:
    start: float  # seconds
    end: float  # seconds, filled in after parsing
    text: str


@dataclass
class Lyrics:
    lines: list[LyricLine] = field(default_factory=list)
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    offset: float = 0.0  # seconds, already applied to line times


def _fraction_to_seconds(frac: str | None) -> float:
    if not frac:
        return 0.0
    return int(frac) / (10 ** len(frac))


def parse_lrc(text: str, audio_duration: float | None = None) -> Lyrics:
    """Parse LRC content into timed, ordered lyric lines.

    Supports multiple time tags per line, metadata tags ([ti:], [ar:],
    [al:], [offset:] in milliseconds), and blank timed lines, which act as
    end markers for the preceding line (instrumental breaks).
    """
    lyrics = Lyrics()
    timed: list[tuple[float, str]] = []

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        meta = META_TAG.match(line)
        if meta:
            key, value = meta.group(1).lower(), meta.group(2)
            if key == "ti":
                lyrics.title = value or None
            elif key == "ar":
                lyrics.artist = value or None
            elif key == "al":
                lyrics.album = value or None
            elif key == "offset":
                try:
                    lyrics.offset = int(value) / 1000.0
                except ValueError:
                    pass
            continue

        tags = list(TIME_TAG.finditer(line))
        if not tags:
            continue
        content = line[tags[-1].end():].strip()
        for tag in tags:
            minutes, seconds, frac = tag.group(1), tag.group(2), tag.group(3)
            t = int(minutes) * 60 + int(seconds) + _fraction_to_seconds(frac)
            timed.append((t, content))

    timed.sort(key=lambda item: item[0])

    # Apply offset ([offset:+500] shifts lyrics 500 ms earlier per de-facto spec).
    if lyrics.offset:
        timed = [(max(0.0, t - lyrics.offset), s) for t, s in timed]

    for i, (start, content) in enumerate(timed):
        if not content:
            continue  # blank marker: only bounds the previous line's end
        if i + 1 < len(timed):
            end = timed[i + 1][0]
        elif audio_duration is not None:
            end = audio_duration
        else:
            end = start + DEFAULT_LAST_LINE_HOLD
        end = max(end, start + 0.5)  # never shorter than half a second
        lyrics.lines.append(LyricLine(start=start, end=end, text=content))

    return lyrics


def load_lrc(path: str | Path, audio_duration: float | None = None) -> Lyrics:
    return parse_lrc(Path(path).read_text(encoding="utf-8"), audio_duration)
