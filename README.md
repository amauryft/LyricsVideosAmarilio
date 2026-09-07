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
  on the same EP share that EP's brand, cover, and background. The
  *Simplesmente Graça* EP's opening track is titled **Abundante Graça**
  (retitled 2026-09-05; the EP name and cover keep "Simplesmente Graça").
  As of 2026-09-05 all 16 videos are rendered and delivered.
- **Next up — the *Peregrino* album (CD2, 13 tracks)**: official lyrics
  (`assets/references/CD2 PEREGRINO as Letras.pdf`, staged per-song in
  `songs/peregrino/`) and audio (branch
  `claude/lyrics-videos-project-cx2e7p`, root MP3s named "NN TÍTULO.mp3"
  in decomposed Unicode — address them with shell globs) arrived
  2026-09-07. Timed lyrics are DONE for all 13 tracks
  (`songs/<slug>.raw.lrc` + final `songs/<slug>.lrc`). Still missing:
  the album art as files (`assets/albums/peregrino/cover.png` + `bg.png`)
  and `brands/peregrino.json` — see `songs/peregrino/README.md`.
- **Recordings can deviate from the PDF**: match what is actually sung.
  Known case: the *Ele é Bom Demais* recording skips the "A ira do meu
  Senhor" verse entirely (chorus + verse 2 only). When a transcription
  shows a suspicious silence, cut that audio window with ffmpeg and
  re-transcribe just the clip before assuming lyrics are there.
- **Source of truth for lyrics**: the official lyrics in
  `assets/references/MUSICAS GRAVADAS p Lyric videos.pdf`. Transcriptions
  (`songs/*.raw.lrc`) only provide timing anchors; the words always come
  from the PDF.
- **Thumbnails / intro slides**: regenerate with `python3
  tools/make_thumbs.py` (all songs + contact sheet). Typography is
  auto-fitted per title; the song list and song→brand mapping live in that
  script.
- **Videos are NOT stored in git.** `videos/` is gitignored. Long-term
  storage is the Google Drive folder **[Lyrics Videos
  Amarilio](https://drive.google.com/drive/folders/1qQ9wzEBnT16A8CZn-XjFKaWYevo4W-7d)**.
  Delivery of a finished render — **chat is the primary channel** (the
  user downloads from the conversation, not from GitHub): chat uploads
  cap at 30 MiB per file, so make a compressed single-file copy that fits
  (two-pass x264 sized to ~28 MiB, `-c:a aac -b:a 128k -movflags
  +faststart`, still 1080p) and send that ONE file. Never send split
  ".partNN" files to the user — reassembling them is not something they
  can do. The full-quality master additionally rides the temporary
  `videos-delivery` branch as archive (GitHub caps files at 100 MiB =
  104,857,600 bytes; split bigger masters there with `split -b 70m` plus
  a `<SONG>-REASSEMBLE.md`, pattern in the branch). Masters go to Drive,
  then the branch commits can be deleted — it is a transfer pipe, not
  storage. The Drive MCP connector cannot upload video-sized files.
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

On step 3, the reliable pattern (used for all 10 videos on 2026-09-05):
keep the raw transcription as `songs/<slug>.raw.lrc` (timing anchors
only), then write the final `.lrc` with the official PDF lines placed on
those anchors — where whisper merged several lines into one segment,
space the official lines evenly across the segment's time span. Blank
timed lines mark instrumental breaks. Verify a frame or two of a
`--preview` render before committing to the full encode.

### Remote sandbox setup (Claude Code on the web)

The cloud container starts empty and `apt-get` and YouTube are blocked by
the network policy. What works:

- **ffmpeg/ffprobe**: static build from BtbN's GitHub *release* assets
  (`github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz`
  → copy `bin/ffmpeg` + `bin/ffprobe` to `/usr/local/bin`). GitHub
  release downloads pass the proxy; `raw.githubusercontent.com` and apt
  mirrors do not.
- **Font**: every brand uses **Libre Caslon Text** only — fetch the ttf
  URLs from `fonts.googleapis.com/css2?family=Libre+Caslon+Text`, save
  to `~/.fonts`, run `fc-cache -f`.
- **pip**: `sherpa-onnx numpy pillow pypdf` (pillow for the contact
  sheet, pypdf to read the lyrics PDF). Whisper models per the
  sherpa-onnx one-time setup below.

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
