#!/usr/bin/env python3
"""Derive a brand's `lyric_scale` from its wrap budget.

How large the lyrics can be set is decided by one question: how many rows
is a single lyric line allowed to occupy? Allow none and the album's
longest line drags every song down; allow one wrap and the type roughly
doubles. This finds the largest size at which no line in the album needs
more rows than the budget, and prints it as the `lyric_scale` to put in
the brand JSON.

    python3 tools/lyric_scale.py brands/vasos-de-barro.json songs/vasos-de-barro/*.txt

Lines come from the staged official lyrics (or any .txt/.lrc); '#'
comments, blank lines and '(section)' markers are skipped.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lyricsvideo.assgen import SHOWCASE, _font_scale, wrap_lyric  # noqa: E402
from lyricsvideo.brand import load_brand  # noqa: E402
from lyricsvideo.themes import THEMES  # noqa: E402

LRC_TS = re.compile(r"^\[\d+:\d+(?:\.\d+)?\]")


def read_lines(paths) -> list[str]:
    out = []
    for p in paths:
        for raw in Path(p).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("[") and not LRC_TS.match(line):
                continue  # [ti:]/[ar:] tags
            line = LRC_TS.sub("", line).strip()
            if not line or line.startswith("("):
                continue
            out.append(line)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brand")
    ap.add_argument("lyrics", nargs="+", help="Staged .txt or timed .lrc files")
    ap.add_argument("--height", type=int, default=1080)
    ap.add_argument("--width", type=int, default=1920)
    args = ap.parse_args(argv)

    brand = load_brand(args.brand)
    theme = brand.apply_to(THEMES["midnight"])
    font = theme.font
    scale = _font_scale(font)
    bold = getattr(brand, "lyric_bold", True)
    italic = getattr(brand, "lyric_italic", False)

    g = SHOWCASE
    avail = args.width - round(args.width * g["lyr_left"]) - round(args.width * g["lyr_right"])
    lines = read_lines(args.lyrics)
    if not lines:
        print("error: no lyric lines found", file=sys.stderr)
        return 1

    print(f"{len(lines)} lines · {font} · column {avail}px\n")
    print(f"{'budget':>16s} {'size':>7s} {'lyric_scale':>12s}   longest line that binds")
    for budget in (1, 2, 3):
        lo, hi = 20.0, 400.0
        for _ in range(48):
            mid = (lo + hi) / 2
            if all(wrap_lyric(t, font, mid, avail, bold, italic, budget)[1] for t in lines):
                lo = mid
            else:
                hi = mid
        # The line that fails first just above the limit is what binds.
        binder = next(
            (t for t in lines
             if not wrap_lyric(t, font, lo * 1.02, avail, bold, italic, budget)[1]),
            "",
        )
        cap = args.height * 0.090
        label = f"{budget} row" + ("" if budget == 1 else "s") + "/line"
        print(f"{label:>16s} {lo * scale:6.0f}px {lo / cap:12.3f}   {binder[:44]}")

    print("\nPut the chosen scale in the brand as \"lyric_scale\"; the fitter "
          "still\nre-checks every song, so a song with shorter lines simply "
          "stops at the cap.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
