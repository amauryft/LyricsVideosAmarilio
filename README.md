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

## Project guide (how this catalog is produced)

These are the standing rules for the whole project:

- **Catalog**: 16 songs — 4 EPs × 3 tracks (*Ainda é Tempo*, *Simplesmente
  Graça*, *Sessenteando*, *Ele é Bom Demais*) plus 4 singles (*Como Você
  Está?*, *Salmodiando*, *Redes Espirituais*, *Louvor com Frevor*). Tracks
  on the same EP share that EP's brand, cover, and background.
- **Source of truth for lyrics**: the official lyrics in
  `assets/references/MUSICAS GRAVADAS p Lyric videos.pdf`. Transcriptions
  (`songs/*.raw.lrc`) only provide timing anchors; the words always come
  from the PDF.
- **Thumbnails / intro slides**: regenerate with `python3
  tools/make_thumbs.py` (all songs + contact sheet). Typography is
  auto-fitted per title; the song list and song→brand mapping live in that
  script.
- **Videos are NOT stored in git.** `videos/` is gitignored (GitHub's file
  limits don't fit them). Final renders are delivered as downloads and
  stored in the Google Drive folder **[Lyrics Videos
  Amarilio](https://drive.google.com/drive/folders/1qQ9wzEBnT16A8CZn-XjFKaWYevo4W-7d)**.
- **Final output format — must be YouTube-ready**: 1920×1080, MP4 with
  faststart, H.264 yuv420p 30fps progressive, AAC 192k 44.1kHz, CRF 18
  (the renderer's defaults already produce exactly this). Verify each
  final render with `ffprobe` before delivery. Use `--preview` and/or
  `--resolution 960x540` for test renders; work one video at a time.
- **Harmony rule**: in the showcase layout the live waveform matches the
  highlighted lyric color (automatic in the renderer).

## Per-song workflow (the pattern)

For each new song, from the repo root:

```bash
# 1. Put the audio in songs/
cp ~/Downloads/minha-musica.mp3 songs/

# 2. Transcribe the sung lyrics to a timed .lrc (Brazilian Portuguese: -l pt)
python3 -m lyricsvideo transcribe songs/minha-musica.mp3 -l pt --title "Minha Música"

# 3. Review songs/minha-musica.lrc — fix words, adjust timings

# 4. Render with the brand
python3 -m lyricsvideo render songs/minha-musica.mp3 songs/minha-musica.lrc \
    --brand brands/sessenteando.json -o output/minha-musica.mp4
```

Use `--preview 30` on step 4 while iterating; drop it for the final render.

### Transcription backends

`transcribe` uses whichever backend is available:

- **faster-whisper** (`pip install faster-whisper`) — models auto-download
  from Hugging Face.
- **sherpa-onnx** (`pip install sherpa-onnx numpy`) — fully offline; used
  automatically when a models directory exists (default `/home/user/models`,
  override with `LYRICSVIDEO_SHERPA_MODELS`). One-time setup:

```bash
mkdir -p /home/user/models && cd /home/user/models
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-turbo.tar.bz2
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx
tar xjf sherpa-onnx-whisper-turbo.tar.bz2 && rm sherpa-onnx-whisper-turbo.tar.bz2
```

## Brand configs

A brand JSON (see `brands/sessenteando.json`) defines a channel's look:
fonts, colors, the `columns` magazine layout, background image and wash,
album cover, and credits. Render any song with `--brand` to apply it.
The Sessenteando brand needs the Playfair Display font installed
(`fc-list | grep Playfair` to check; download from Google Fonts).

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
