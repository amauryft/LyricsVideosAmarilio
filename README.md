# LyricsVideosAmarilio

Render polished lyrics videos from an audio file and a timed `.lrc` lyrics file — no video editor needed. Pure Python (stdlib only) driving `ffmpeg`.

## What it does

- Parses standard **LRC** files (timestamps, metadata tags, `[offset:]`, repeated-chorus multi-tags, blank lines as instrumental breaks)
- Generates styled **ASS subtitles**: centered current line with fade in/out, a dimmed preview of the upcoming line, and an automatic title card from `[ti:]`/`[ar:]` tags
- Builds the video with ffmpeg: animated gradient background (5 built-in themes) **or** your own image/video background, optional audio **waveform** overlay, H.264 + AAC output ready for YouTube

## Requirements

- Python ≥ 3.10
- `ffmpeg` and `ffprobe` on your PATH (with libass, which standard builds include)

## Install

```bash
pip install -e .
# or skip installing and use: python3 -m lyricsvideo ...
```

## Usage

```bash
# Basic render → output/song.mp4
lyricsvideo render song.mp3 song.lrc

# Pick a theme, add a waveform, choose the output path
lyricsvideo render song.mp3 song.lrc --theme sunset --waveform -o my-video.mp4

# Use your own background image or video instead of the gradient
lyricsvideo render song.mp3 song.lrc --background cover-art.jpg

# Vertical format for Shorts/Reels/TikTok
lyricsvideo render song.mp3 song.lrc --resolution 1080x1920

# Fast iteration: render only the first 20 seconds
lyricsvideo render song.mp3 song.lrc --preview 20

# See all themes
lyricsvideo themes
```

### Themes

| Theme      | Look                                    |
|------------|-----------------------------------------|
| `midnight` | Deep blue night sky, soft white lyrics (default) |
| `sunset`   | Warm orange-to-purple gradient          |
| `neon`     | Black background, electric cyan lyrics  |
| `minimal`  | Clean light background, dark serif lyrics |
| `forest`   | Dark green tones, warm cream lyrics     |

## LRC format quick reference

```
[ti:Song Title]
[ar:Artist Name]
[offset:0]

[00:04.00]First lyric line
[00:07.50]Second lyric line
[00:11.00]
[00:15.00]A blank timed line above marks an instrumental break
```

- `[mm:ss.xx]text` — the line appears at that time and stays until the next timestamp
- Multiple tags on one line (`[00:10.00][01:30.00]chorus`) repeat the line
- A timestamp with no text ends the previous line early (nothing shown during the break)
- The title card only appears if the first lyric starts at least 2.5 s in

## Try the demo

Generates a synthetic 32-second track and renders it with the demo lyrics:

```bash
./examples/make_demo.sh          # midnight theme
./examples/make_demo.sh sunset   # any theme name
```

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Project layout

```
lyricsvideo/
  lrc.py      LRC parsing → timed lyric lines
  themes.py   Visual theme presets
  assgen.py   Styled ASS subtitle generation (fades, title card, preview line)
  render.py   ffmpeg orchestration (background, waveform, subtitle burn, encode)
  cli.py      Command line interface
examples/     Demo lyrics + demo script
tests/        Unit tests (stdlib unittest)
```
