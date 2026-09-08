#!/usr/bin/env python3
"""Regenerate the thumbnail/intro composition slides and their contact sheet.

For every track in the catalog this renders the showcase intro screen (big
cover, fitted title, author, "Lyrics Video" tag) exactly as the video
renderer draws it, using that release's own brand config and the same ASS
generation code, and saves it next to the release's renders as
catalog/<type>/<release>/renders/<slug>-thumb.png. Then it assembles
catalog/contact-sheets/SHEET-thumbnails.png.

The song list comes from the release manifests, so a new release needs no
edit here — only its release.json and brand.json.

Usage, from the repo root:
    python3 tools/make_thumbs.py            # every branded track + sheet
    python3 tools/make_thumbs.py salmodiando ta-com-sede   # just these + sheet
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lyricsvideo.assgen import SHOWCASE, build_showcase_ass  # noqa: E402
from lyricsvideo.brand import load_brand  # noqa: E402
from lyricsvideo.catalog import iter_tracks  # noqa: E402
from lyricsvideo.lrc import Lyrics  # noqa: E402
from lyricsvideo.themes import THEMES  # noqa: E402

W, H = 1920, 1080
SHEET = ROOT / "catalog" / "contact-sheets" / "SHEET-thumbnails.png"


def branded_tracks():
    """(release, track) for every track whose release has a brand config."""
    return [(r, t) for r, t in iter_tracks() if r.brand is not None]


def make_thumb(title: str, brand_path: Path, out: Path) -> None:
    brand = load_brand(brand_path)
    theme = brand.apply_to(THEMES["midnight"])
    lyrics = Lyrics(lines=[], title=title, artist=brand.artist)
    ass_text = build_showcase_ass(
        lyrics, theme, brand, W, H, duration=8.0, intro_end=6.0,
        song_title=title, author=brand.artist,
    )

    g = SHOWCASE
    big_w = round(W * g["intro_cover_w"])
    big_x = round(W * g["intro_cover_x"])
    border_color = brand.cover_border or theme.text_color
    b = max(2, round(W * 0.004))

    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="thumb-") as tmp:
        ass_file = Path(tmp) / "intro.ass"
        ass_file.write_text(ass_text, encoding="utf-8")
        filters = (
            f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},setsar=1[bg];"
            f"[1:v]scale={big_w}:-1,pad=iw+{2*b}:ih+{2*b}:{b}:{b}"
            f":color=0x{border_color.lstrip('#')}[cover];"
            f"[bg][cover]overlay=x={big_x}:y=(H-h)/2[wcov];"
            f"[wcov]ass=filename={ass_file.name}[out]"
        )
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1", "-framerate", "30", "-i", str(brand.background),
            "-loop", "1", "-framerate", "30", "-i", str(brand.cover),
            "-filter_complex", filters, "-map", "[out]",
            "-ss", "2", "-frames:v", "1", str(out),
        ]
        subprocess.run(cmd, cwd=tmp, check=True)


def make_sheet(out: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont

    tracks = branded_tracks()
    cols, tile_w, gap, label_h = 3, 630, 8, 34
    tile_h = round(tile_w * H / W)
    rows = -(-len(tracks) // cols)
    sheet = Image.new(
        "RGB",
        (cols * tile_w + (cols - 1) * gap, rows * (tile_h + label_h) + (rows - 1) * gap),
        "#191919",
    )
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 22
        )
    except OSError:
        font = ImageFont.load_default()
    for i, (_release, track) in enumerate(tracks):
        x = (i % cols) * (tile_w + gap)
        y = (i // cols) * (tile_h + label_h + gap)
        draw.text((x + 4, y + 5), track.title, fill="#f0f0f0", font=font)
        img = Image.open(track.thumb).resize((tile_w, tile_h), Image.LANCZOS)
        sheet.paste(img, (x, y + label_h))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def main() -> None:
    only = set(sys.argv[1:])
    known = {t.slug for _, t in branded_tracks()}
    for slug in sorted(only - known):
        print(f"warning: no branded track {slug!r} in the catalog", file=sys.stderr)
    for release, track in branded_tracks():
        if only and track.slug not in only:
            continue
        make_thumb(track.title, release.brand, track.thumb)
        print(f"  {release.slug}/{track.thumb.name}")
    make_sheet(SHEET)
    print(f"  {SHEET.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
