"""Brand configuration: a JSON file describing a channel's visual identity.

Example (brands/sessenteando.json):

{
  "layout": "columns",
  "font": "Playfair Display",
  "text_color": "#203a75",
  "dim_color": "#93a3c6",
  "title_color": "#2743c8",
  "credit_color": "#174d3d",
  "background": "assets/ocean-wash.png",
  "bg_wash": 0.35,
  "cover": "assets/cover.png",
  "album": "Sessenteando",
  "artist": "Amarilio Fontenele",
  "credit": "Letra e música\nAmarílio Fontenele",
  "lines": 2
}

Paths are resolved relative to the JSON file's directory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path

from .themes import Theme

_THEME_KEYS = {
    "font", "text_color", "dim_color", "outline_color",
    "bg_top", "bg_bottom", "wave_color",
}
_BRAND_KEYS = _THEME_KEYS | {
    "layout", "title_color", "credit_color", "background", "bg_wash",
    "cover", "album", "artist", "credit", "lines",
    "block_bg", "block_alpha", "block_text_color", "cover_border",
    "label", "intro",
}


@dataclass
class Brand:
    theme_overrides: dict = field(default_factory=dict)
    layout: str | None = None  # "showcase", "columns" or None (classic centered)
    title_color: str = "#2743c8"
    credit_color: str = "#174d3d"
    background: Path | None = None
    bg_wash: float = 0.35
    cover: Path | None = None
    album: str | None = None
    artist: str | None = None
    credit: str | None = None
    lines: int | None = None
    # showcase layout
    block_bg: str = "#ffffff"  # title/author strip fill
    block_alpha: float = 0.6
    block_text_color: str | None = None  # defaults to the theme text color
    cover_border: str | None = None  # hard border around the cover art
    label: str = "Lyrics Video"  # small label on the intro screen
    intro: bool = True  # title moment before the first lyric

    def apply_to(self, theme: Theme) -> Theme:
        return replace(theme, **self.theme_overrides) if self.theme_overrides else theme


def load_brand(path: str | Path) -> Brand:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(data) - _BRAND_KEYS
    if unknown:
        raise ValueError(f"Unknown brand keys in {path}: {', '.join(sorted(unknown))}")

    brand = Brand(theme_overrides={k: data[k] for k in _THEME_KEYS if k in data})
    for key in ("layout", "title_color", "credit_color", "album", "artist", "credit",
                "block_bg", "block_text_color", "cover_border", "label"):
        if key in data:
            setattr(brand, key, data[key])
    if "bg_wash" in data:
        brand.bg_wash = float(data["bg_wash"])
    if "block_alpha" in data:
        brand.block_alpha = float(data["block_alpha"])
    if "lines" in data:
        brand.lines = int(data["lines"])
    if "intro" in data:
        brand.intro = bool(data["intro"])
    for key in ("background", "cover"):
        if data.get(key):
            resolved = (path.parent / data[key]).resolve()
            if not resolved.is_file():
                raise ValueError(f"Brand {key} file not found: {resolved}")
            setattr(brand, key, resolved)
    return brand
