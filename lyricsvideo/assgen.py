"""Generate styled ASS subtitles from parsed lyrics."""

from __future__ import annotations

from .lrc import Lyrics, LyricLine
from .themes import Theme

FADE_MS = 250
BLOCK_GAP_BREAK = 2.5  # a silence this long starts a new lyric block
TITLE_CARD_MIN_LEAD = 2.5  # only show a title card if lyrics start this late
TITLE_CARD_MAX = 6.0


def _ass_color(hex_color: str, alpha: int = 0) -> str:
    """#RRGGBB -> &HAABBGGRR (ASS is little-endian BGR with inverted alpha)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def _ass_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def _color_tag(hex_color: str) -> str:
    """Inline primary-colour override, e.g. {\\1c&HBBGGRR&}."""
    h = hex_color.lstrip("#")
    return f"\\1c&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def group_blocks(
    lines: list[LyricLine], block_size: int, gap_break: float = BLOCK_GAP_BREAK
) -> list[list[LyricLine]]:
    """Chunk lines into stanzas of up to block_size, breaking at silences."""
    blocks: list[list[LyricLine]] = []
    current: list[LyricLine] = []
    for line in lines:
        if current and (
            len(current) == block_size or line.start - current[-1].end > gap_break
        ):
            blocks.append(current)
            current = []
        current.append(line)
    if current:
        blocks.append(current)
    return blocks


def build_ass(
    lyrics: Lyrics,
    theme: Theme,
    width: int,
    height: int,
    show_upcoming: bool = True,
    title: str | None = None,
    artist: str | None = None,
    block_size: int = 1,
) -> str:
    """Render lyrics to an ASS document sized for the given resolution.

    With block_size > 1, lyrics are shown as stanzas of up to that many
    stacked lines, the currently sung line highlighted and the rest dimmed.
    """
    main_size = max(24, round(height * 0.062))
    block_line_size = max(20, round(height * 0.052))
    next_size = max(16, round(main_size * 0.55))
    title_size = max(28, round(height * 0.075))
    sub_size = max(18, round(title_size * 0.5))
    outline = max(1, round(main_size / 18))

    header = f"""[Script Info]
Title: LyricsVideosAmarilio
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Current,{theme.font},{main_size},{_ass_color(theme.text_color)},{_ass_color(theme.text_color)},{_ass_color(theme.outline_color)},{_ass_color("#000000", 128)},1,0,0,0,100,100,0,0,1,{outline},{outline},5,60,60,0,1
Style: Upcoming,{theme.font},{next_size},{_ass_color(theme.dim_color)},{_ass_color(theme.dim_color)},{_ass_color(theme.outline_color)},{_ass_color("#000000", 160)},0,0,0,0,100,100,0,0,1,{max(1, outline - 1)},0,8,60,60,{round(height * 0.72)},1
Style: TitleCard,{theme.font},{title_size},{_ass_color(theme.text_color)},{_ass_color(theme.text_color)},{_ass_color(theme.outline_color)},{_ass_color("#000000", 128)},1,0,0,0,100,100,2,0,1,{outline},{outline},5,60,60,0,1
Style: TitleSub,{theme.font},{sub_size},{_ass_color(theme.dim_color)},{_ass_color(theme.dim_color)},{_ass_color(theme.outline_color)},{_ass_color("#000000", 160)},0,0,0,0,100,100,3,0,1,{max(1, outline - 1)},0,5,60,60,{round(height * 0.14)},1
Style: Block,{theme.font},{block_line_size},{_ass_color(theme.text_color)},{_ass_color(theme.text_color)},{_ass_color(theme.outline_color)},{_ass_color("#000000", 128)},0,0,0,0,100,100,0,0,1,{outline},{outline},5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events: list[str] = []
    fade = f"{{\\fad({FADE_MS},{FADE_MS})}}"

    card_title = title or lyrics.title
    card_artist = artist or lyrics.artist
    first_start = lyrics.lines[0].start if lyrics.lines else TITLE_CARD_MAX
    if card_title and first_start >= TITLE_CARD_MIN_LEAD:
        card_end = min(first_start - 0.4, TITLE_CARD_MAX)
        events.append(
            f"Dialogue: 0,{_ass_time(0.3)},{_ass_time(card_end)},TitleCard,,0,0,0,,{fade}{_escape(card_title)}"
        )
        if card_artist:
            events.append(
                f"Dialogue: 0,{_ass_time(0.3)},{_ass_time(card_end)},TitleSub,,0,0,0,,{fade}{_escape(card_artist)}"
            )

    if block_size > 1:
        active_tag = "{" + _color_tag(theme.text_color) + "\\b1}"
        dim_tag = "{" + _color_tag(theme.dim_color) + "\\b0}"
        for block in group_blocks(lyrics.lines, block_size):
            for i, line in enumerate(block):
                start = line.start
                end = block[i + 1].start if i + 1 < len(block) else line.end
                if end <= start:
                    continue
                text = "\\N".join(
                    f"{active_tag if j == i else dim_tag}{_escape(other.text)}"
                    for j, other in enumerate(block)
                )
                fad = f"{{\\fad({FADE_MS if i == 0 else 0},{FADE_MS if i == len(block) - 1 else 0})}}"
                events.append(
                    f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},Block,,0,0,0,,{fad}{text}"
                )
    else:
        for i, line in enumerate(lyrics.lines):
            events.append(
                f"Dialogue: 1,{_ass_time(line.start)},{_ass_time(line.end)},Current,,0,0,0,,{fade}{_escape(line.text)}"
            )
            if show_upcoming and i + 1 < len(lyrics.lines):
                nxt = lyrics.lines[i + 1]
                # Only preview the next line while the current one is on screen
                # and the next actually follows it directly.
                if nxt.start - line.end <= 1.0:
                    events.append(
                        f"Dialogue: 0,{_ass_time(line.start)},{_ass_time(min(line.end, nxt.start))},Upcoming,,0,0,0,,{fade}{_escape(nxt.text)}"
                    )

    return header + "\n".join(events) + "\n"
