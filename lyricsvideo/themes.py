"""Visual theme presets for lyrics videos.

Colors are plain ``#RRGGBB`` hex strings; conversion to the formats ffmpeg
and ASS expect happens where they are used.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    name: str
    description: str
    # Animated background gradient (two stops).
    bg_top: str
    bg_bottom: str
    # Lyrics text.
    font: str
    text_color: str
    outline_color: str
    # Dimmed color used for the upcoming-line preview and title card subtitle.
    dim_color: str
    # Waveform overlay color (when --waveform is enabled).
    wave_color: str


THEMES: dict[str, Theme] = {
    t.name: t
    for t in (
        Theme(
            name="midnight",
            description="Deep blue night sky, soft white lyrics",
            bg_top="#0f1b3d",
            bg_bottom="#040711",
            font="DejaVu Sans",
            text_color="#f5f7ff",
            outline_color="#0a1230",
            dim_color="#8a94b8",
            wave_color="#5b7bd6",
        ),
        Theme(
            name="sunset",
            description="Warm orange-to-purple gradient",
            bg_top="#ff7e47",
            bg_bottom="#5b2a86",
            font="DejaVu Sans",
            text_color="#fff8f0",
            outline_color="#3d1c59",
            dim_color="#e8c8b8",
            wave_color="#ffd166",
        ),
        Theme(
            name="neon",
            description="Black background, electric cyan lyrics",
            bg_top="#101018",
            bg_bottom="#000000",
            font="DejaVu Sans",
            text_color="#2de2e6",
            outline_color="#0b3c3e",
            dim_color="#1a7a7d",
            wave_color="#f6019d",
        ),
        Theme(
            name="minimal",
            description="Clean light background, dark lyrics",
            bg_top="#f7f5f0",
            bg_bottom="#e8e4da",
            font="DejaVu Serif",
            text_color="#1f1d1a",
            outline_color="#f7f5f0",
            dim_color="#9a958c",
            wave_color="#b0a99c",
        ),
        Theme(
            name="forest",
            description="Dark green tones, warm cream lyrics",
            bg_top="#1d3b2a",
            bg_bottom="#0a1510",
            font="DejaVu Sans",
            text_color="#f2ead9",
            outline_color="#122418",
            dim_color="#87977f",
            wave_color="#6faf7f",
        ),
    )
}

DEFAULT_THEME = "midnight"


def get_theme(name: str) -> Theme:
    try:
        return THEMES[name]
    except KeyError:
        options = ", ".join(sorted(THEMES))
        raise ValueError(f"Unknown theme {name!r}. Available: {options}") from None
