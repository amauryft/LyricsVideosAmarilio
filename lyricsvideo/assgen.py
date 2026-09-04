"""Generate styled ASS subtitles from parsed lyrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .lrc import Lyrics, LyricLine
from .themes import Theme

if TYPE_CHECKING:
    from .brand import Brand

# Showcase layout geometry, as fractions of frame width/height.
# Derived from the reference layout images (3840x2160 masters).
SHOWCASE = {
    "cover_x": 0.0575, "cover_y": 0.111, "cover_w": 0.2275,
    "block_x": 0.0575, "block_y": 0.573, "block_w": 0.2275, "block_h": 0.105,
    "lyr_left": 0.35, "lyr_right": 0.08,
    "intro_cover_w": 0.34, "intro_cover_x": 0.059, "intro_text_x": 0.45,
}

# Roughly how many characters of the block title fit on one line.
_BLOCK_TITLE_CHARS_PER_LINE = 19


def showcase_block_metrics(title: str | None) -> tuple[int, float, float]:
    """(title_lines, strip_height_frac, author_offset_frac) for the strip.

    The strip grows and the author line moves down when the song title
    wraps, mirroring the reference layouts.
    """
    lines = max(1, -(-len(title or "") // _BLOCK_TITLE_CHARS_PER_LINE))
    lines = min(lines, 3)
    strip_h = 0.105 + (lines - 1) * 0.048
    author_off = 0.014 + lines * 0.050
    return lines, strip_h, author_off

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
    h = hex_color.lstrip("#").upper()
    return f"\\1c&H{h[4:6]}{h[2:4]}{h[0:2]}&"


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


def build_showcase_ass(
    lyrics: Lyrics,
    theme: Theme,
    brand: "Brand",
    width: int,
    height: int,
    duration: float,
    intro_end: float,
    block_size: int = 4,
    song_title: str | None = None,
    author: str | None = None,
) -> str:
    """The album showcase layout, from the reference art:

    Cover art top-left with a translucent title/author strip below it,
    large left-aligned serif lyrics in the open center-right area
    (block_size lines, sung line full color, others dimmed), and an
    intro title screen (big cover + song title/author/label) that the
    ffmpeg side pairs with a larger cover overlay until intro_end.
    """
    g = SHOWCASE
    lyr_size = max(24, round(height * 0.058))
    block_title_size = max(18, round(height * 0.040))
    block_author_size = max(12, round(height * 0.024))
    intro_title_size = max(28, round(height * 0.082))
    intro_author_size = max(18, round(height * 0.046))
    intro_label_size = max(14, round(height * 0.036))

    block_text = brand.block_text_color or theme.text_color
    pad_x = round(width * 0.012)
    hidden = _ass_color("#000000", 255)
    _, _, author_off = showcase_block_metrics(song_title or lyrics.title or "")
    # Confine the block texts to the strip so long titles wrap inside it.
    block_mr = width - round(width * (g["block_x"] + g["block_w"])) + pad_x

    def style(name, size, color, bold, align, ml, mr, mv):
        return (
            f"Style: {name},{theme.font},{size},{_ass_color(color)},{_ass_color(color)},"
            f"{hidden},{hidden},{bold},0,0,0,100,100,0,0,1,0,0,{align},{ml},{mr},{mv},1"
        )

    header = f"""[Script Info]
Title: LyricsVideosAmarilio
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style("Lyr", lyr_size, theme.text_color, 0, 4, round(width * g["lyr_left"]), round(width * g["lyr_right"]), 0)}
{style("BlockTitle", block_title_size, block_text, 1, 7, round(width * g["block_x"]) + pad_x, block_mr, round(height * (g["block_y"] + 0.014)))}
{style("BlockAuthor", block_author_size, block_text, 0, 7, round(width * g["block_x"]) + pad_x, block_mr, round(height * (g["block_y"] + author_off)))}
{style("IntroTitle", intro_title_size, theme.text_color, 1, 7, round(width * g["intro_text_x"]), round(width * 0.05), round(height * 0.20))}
{style("IntroAuthor", intro_author_size, theme.text_color, 0, 7, round(width * g["intro_text_x"]), round(width * 0.05), round(height * 0.47))}
{style("IntroLabel", intro_label_size, theme.dim_color, 1, 7, round(width * g["intro_text_x"]), round(width * 0.05), round(height * 0.68))}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events: list[str] = []
    title = song_title or lyrics.title or ""
    author = author or lyrics.artist or ""

    if intro_end > 0:
        fad = "{\\fad(400,400)}"
        if title:
            events.append(
                f"Dialogue: 0,{_ass_time(0.2)},{_ass_time(intro_end)},IntroTitle,,0,0,0,,{fad}{_escape(title)}"
            )
        if author:
            events.append(
                f"Dialogue: 0,{_ass_time(0.2)},{_ass_time(intro_end)},IntroAuthor,,0,0,0,,{fad}{_escape(author)}"
            )
        if brand.label:
            events.append(
                f"Dialogue: 0,{_ass_time(0.2)},{_ass_time(intro_end)},IntroLabel,,0,0,0,,{fad}{_escape(brand.label)}"
            )

    fad_in = "{\\fad(400,0)}"
    if title:
        events.append(
            f"Dialogue: 0,{_ass_time(intro_end)},{_ass_time(duration)},BlockTitle,,0,0,0,,{fad_in}{_escape(title)}"
        )
    if author:
        events.append(
            f"Dialogue: 0,{_ass_time(intro_end)},{_ass_time(duration)},BlockAuthor,,0,0,0,,{fad_in}{_escape(author)}"
        )

    active_tag = "{" + _color_tag(theme.text_color) + "}"
    dim_tag = "{" + _color_tag(theme.dim_color) + "}"
    for block in group_blocks(lyrics.lines, max(1, block_size)):
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
                f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},Lyr,,0,0,0,,{fad}{text}"
            )

    return header + "\n".join(events) + "\n"


def build_columns_ass(
    lyrics: Lyrics,
    theme: Theme,
    width: int,
    height: int,
    duration: float,
    block_size: int = 2,
    song_title: str | None = None,
    credit: str | None = None,
    album: str | None = None,
    artist: str | None = None,
    title_color: str = "#2743C8",
    credit_color: str = "#174D3D",
) -> str:
    """Three-column magazine layout on a light background.

    Left: album/artist text (the cover image is composited by ffmpeg).
    Center: left-aligned italic lyrics, block_size lines at a time, the
    sung line in full color and the rest dimmed. Long lines wrap inside
    the column. Right: song title and credit, shown for the whole video.
    """
    lyric_size = max(24, round(height * 0.072))
    title_size = max(22, round(height * 0.046))
    credit_size = max(14, round(height * 0.028))
    album_size = max(16, round(height * 0.036))

    margin_lyrics_l = round(width * 0.315)
    margin_lyrics_r = round(width * 0.27)
    margin_side = round(width * 0.055)

    header = f"""[Script Info]
Title: LyricsVideosAmarilio
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ColLyrics,{theme.font},{lyric_size},{_ass_color(theme.text_color)},{_ass_color(theme.text_color)},{_ass_color("#FFFFFF", 255)},{_ass_color("#000000", 255)},0,1,0,0,100,100,0,0,1,0,0,4,{margin_lyrics_l},{margin_lyrics_r},0,1
Style: ColTitle,{theme.font},{title_size},{_ass_color(title_color)},{_ass_color(title_color)},{_ass_color("#FFFFFF", 255)},{_ass_color("#000000", 255)},1,1,0,0,100,100,0,0,1,0,0,9,60,{margin_side},{round(height * 0.105)},1
Style: ColCredit,{theme.font},{credit_size},{_ass_color(credit_color)},{_ass_color(credit_color)},{_ass_color("#FFFFFF", 255)},{_ass_color("#000000", 255)},1,1,0,0,100,100,0,0,1,0,0,9,60,{margin_side},{round(height * 0.185)},1
Style: ColAlbum,{theme.font},{album_size},{_ass_color(theme.text_color)},{_ass_color(theme.text_color)},{_ass_color("#FFFFFF", 255)},{_ass_color("#000000", 255)},1,1,0,0,100,100,0,0,1,0,0,7,{margin_side},60,{round(height * 0.105)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events: list[str] = []
    full = f"0,{_ass_time(0.0)},{_ass_time(duration)}"

    if song_title:
        events.append(f"Dialogue: {full},ColTitle,,0,0,0,,{_escape(song_title)}")
    if credit:
        credit_text = "\\N".join(_escape(part) for part in credit.splitlines())
        events.append(f"Dialogue: {full},ColCredit,,0,0,0,,{credit_text}")
    if album:
        album_text = _escape(album)
        if artist:
            album_text += "\\N" + "{\\fs" + str(round(album_size * 0.72)) + "}" + _escape(artist)
        events.append(f"Dialogue: {full},ColAlbum,,0,0,0,,{album_text}")

    active_tag = "{" + _color_tag(theme.text_color) + "}"
    dim_tag = "{" + _color_tag(theme.dim_color) + "}"
    for block in group_blocks(lyrics.lines, max(1, block_size)):
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
                f"Dialogue: 1,{_ass_time(start)},{_ass_time(end)},ColLyrics,,0,0,0,,{fad}{text}"
            )

    return header + "\n".join(events) + "\n"
