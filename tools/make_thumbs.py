#!/usr/bin/env python3
"""Regenerate the thumbnail/intro composition slides and their contact sheet.

For every song this renders the showcase intro screen (big cover, fitted
title, author, "Lyrics Video" tag) exactly as the video renderer draws it,
using the same brand config and ASS generation code, and saves it to
compositions/<slug>-thumb.png. Then it assembles compositions/SHEET-thumbnails.png.

Usage, from the repo root:
    python3 tools/make_thumbs.py            # all songs + sheet
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
from lyricsvideo.lrc import Lyrics  # noqa: E402
from lyricsvideo.themes import THEMES  # noqa: E402

W, H = 1920, 1080

# slug, display title, brand
SONGS = [
    ("ainda-e-tempo", "Ainda é Tempo", "ainda-e-tempo"),
    ("corriqueiramente", "Corriqueiramente", "ainda-e-tempo"),
    ("quero-lembrar-me", "Quero Lembrar-me do Meu Criador", "ainda-e-tempo"),
    ("sessenteando", "Sessenteando", "sessenteando"),
    ("29-de-dezembro", "29 de Dezembro", "sessenteando"),
    ("cancao-de-perdao-e-paz", "Canção de Perdão e Paz", "sessenteando"),
    ("ele-e-bom-demais", "Ele é Bom Demais", "ele-e-bom-demais"),
    ("por-hoje-estou-limpo", "Por Hoje Estou Limpo", "ele-e-bom-demais"),
    ("ta-com-sede", "Tá com Sede?", "ele-e-bom-demais"),
    ("como-voce-esta", "Como Você Está?", "como-voce-esta"),
    ("salmodiando", "Salmodiando", "salmodiando"),
    ("redes-espirituais", "Redes Espirituais", "redes-espirituais"),
    ("louvor-com-frevor", "Louvor com Frevor", "louvor-com-frevor"),
    ("abundante-graca", "Abundante Graça", "simplesmente-graca"),
    ("reviravolta-de-amor", "Reviravolta de Amor", "simplesmente-graca"),
    ("eu-sei-que-um-dia-vira", "Eu Sei Que Um Dia Virá", "simplesmente-graca"),
]


def make_thumb(slug: str, title: str, brand_slug: str, out: Path) -> None:
    brand = load_brand(ROOT / "brands" / f"{brand_slug}.json")
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

    cols, tile_w, gap, label_h = 3, 630, 8, 34
    tile_h = round(tile_w * H / W)
    rows = -(-len(SONGS) // cols)
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
    for i, (slug, title, _) in enumerate(SONGS):
        x = (i % cols) * (tile_w + gap)
        y = (i // cols) * (tile_h + label_h + gap)
        draw.text((x + 4, y + 5), title, fill="#f0f0f0", font=font)
        img = Image.open(ROOT / "compositions" / f"{slug}-thumb.png").resize(
            (tile_w, tile_h), Image.LANCZOS
        )
        sheet.paste(img, (x, y + label_h))
    sheet.save(out)


def main() -> None:
    only = set(sys.argv[1:])
    for slug, title, brand_slug in SONGS:
        if only and slug not in only:
            continue
        out = ROOT / "compositions" / f"{slug}-thumb.png"
        make_thumb(slug, title, brand_slug, out)
        print(f"  {out.name}")
    make_sheet(ROOT / "compositions" / "SHEET-thumbnails.png")
    print("  SHEET-thumbnails.png")


if __name__ == "__main__":
    main()
