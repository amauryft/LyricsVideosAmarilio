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

- **Everything lives in `catalog/`**, one folder per release, grouped as
  `albums/`, `eps/` and `singles/`. Each release folder holds its own
  `release.json` manifest, `brand.json`, `assets/{graphics,music,references}/`,
  `lyrics/` and `renders/` — always the same shape, so producing the next
  release is the same steps as the last. The layout, the manifest format and
  how to start a release are documented in **[`catalog/README.md`](catalog/README.md)**.
- **Catalog**: 16 songs — 4 EPs × 3 tracks (*Ainda é Tempo*, *Simplesmente
  Graça*, *Sessenteando*, *Ele é Bom Demais*) plus 4 singles (*Como Você
  Está?*, *Salmodiando*, *Redes Espirituais*, *Louvor com Frevor*). Tracks
  on the same EP share that EP's brand, cover, and background. The
  *Simplesmente Graça* EP's opening track is titled **Abundante Graça**
  (retitled 2026-09-05; the EP name and cover keep "Simplesmente Graça").
  As of 2026-09-05 all 16 videos are rendered and delivered.
- **The *Peregrino* album (CD2, 13 tracks)**: DONE — all 13 videos
  rendered and delivered 2026-09-08 (chat copies sent; full-quality
  files on `videos-delivery`, single file per song, pending the Drive
  archive pull). Everything sits under `catalog/albums/peregrino/`: the
  lyrics PDF and the per-track official text in `assets/references/`, the
  13 MP3s in `assets/music/`, timed lyrics in `lyrics/`. The brand
  (`catalog/albums/peregrino/brand.json`) pairs Poppins lyrics/titles with
  Libre Caslon Text credits via the `secondary_font` brand key, and the
  showcase layout auto-fits lyric size per song and hangs the block from
  the top of the album art.
- **The *Vasos de Barro* album (CD1, 11 tracks)**: sources staged in
  `catalog/albums/vasos-de-barro/` (audio + lyrics PDF), no brand and no
  timed lyrics yet — its `release.json` has `"brand": null`. The track
  titles there came from the source filenames; confirm them against the
  PDF when staging the lyrics.
- **Recordings can deviate from the PDF**: match what is actually sung.
  Known case: the *Ele é Bom Demais* recording skips the "A ira do meu
  Senhor" verse entirely (chorus + verse 2 only). When a transcription
  shows a suspicious silence, cut that audio window with ffmpeg and
  re-transcribe just the clip before assuming lyrics are there.
- **Source of truth for lyrics**: the official lyrics document — the
  catalog-wide `catalog/references/MUSICAS GRAVADAS p Lyric videos.pdf` for
  the EPs and singles, or the release's own PDF in its
  `assets/references/`. Transcriptions (`lyrics/<slug>.raw.lrc`) only
  provide timing anchors; the words always come from the PDF.
- **Thumbnails / intro slides**: regenerate with `python3
  tools/make_thumbs.py` (all songs + contact sheet), which writes
  `<release>/renders/<slug>-thumb.png` and
  `catalog/contact-sheets/SHEET-thumbnails.png`. Typography is auto-fitted
  per title; the song list comes from the release manifests, so a new
  release needs no edit to the script.
- **Videos are NOT stored in git.** `<release>/renders/*.mp4` is
  gitignored (the stills beside it are committed). Source audio under
  `<release>/assets/music/` *is* committed on purpose — cloud sessions are
  ephemeral and git is the only copy that survives one. Long-term
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
- **Anticipation rule**: lyrics always run ahead of the audio — every
  line appears ~1.5s early (renderer `--lead`, default 1.5; use up to ~2
  when a song's timings feel late) and a new stanza block appears an
  extra ~1.2s earlier still, so viewers can refocus before the singing
  catches up. Never let the lyrics lag the voice.

## Per-song workflow (the pattern)

Every song sits in a release folder (see
[`catalog/README.md`](catalog/README.md)); `R` below is that folder, e.g.
`catalog/eps/sessenteando`. From the repo root:

```bash
R=catalog/eps/sessenteando

# 1. The audio is already in the release (tools/new_release.py puts it there)
ls $R/assets/music/

# 2. Transcribe the sung lyrics to a timed .lrc (Brazilian Portuguese: -l pt)
python3 -m lyricsvideo transcribe $R/assets/music/01-minha-musica.mp3 \
    -l pt --title "Minha Música" -o $R/lyrics/minha-musica.raw.lrc

# 3. Write $R/lyrics/minha-musica.lrc — official words on the raw anchors

# 4. Render with the release's brand
python3 -m lyricsvideo render $R/assets/music/01-minha-musica.mp3 \
    $R/lyrics/minha-musica.lrc --brand $R/brand.json \
    -o $R/renders/minha-musica.mp4
```

Use `--preview 30` on step 4 while iterating; drop it for the final render.

On step 3, the reliable pattern (used for all 10 videos on 2026-09-05):
keep the raw transcription as `lyrics/<slug>.raw.lrc` (timing anchors
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
- **Fonts**: fetch the ttf URLs from
  `fonts.googleapis.com/css2?family=Libre+Caslon+Text` (and the other
  families named in `catalog/*/*/brand.json` and `catalog/extra-fonts.txt`),
  save to `~/.fonts`, run `fc-cache -f`. The SessionStart hook does this
  automatically.
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

Each release has one `brand.json` beside its `release.json` (see
`catalog/eps/sessenteando/brand.json`) defining its look: fonts, colors,
the layout, background image and wash, album cover, and credits. Its
`background` and `cover` paths resolve relative to the file itself, so
they point into that release's own `assets/graphics/`. Render any song
with `--brand` to apply it. The Sessenteando brand needs the Playfair
Display font installed (`fc-list | grep Playfair` to check; the
SessionStart hook installs every family any brand references, plus those
listed in `catalog/extra-fonts.txt`).

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
catalog/      The music: one folder per release, grouped albums / eps /
              singles, each with its own manifest, brand, assets, lyrics
              and renders. See catalog/README.md.
lyricsvideo/
  lrc.py      LRC parsing → timed lyric lines
  themes.py   Visual theme presets
  assgen.py   Styled ASS subtitle generation (fades, title card, preview line)
  render.py   ffmpeg orchestration (background, waveform, subtitle burn, encode)
  brand.py    Per-release visual identity (brand.json)
  catalog.py  Release/track discovery from the release.json manifests
  cli.py      Command line interface
tools/
  make_thumbs.py   Thumbnails + contact sheet for every release
  new_release.py   Scaffold a new release folder
assets/       Shared engine/demo assets, not owned by any release
examples/     Demo lyrics + demo script
tests/        Unit tests (stdlib unittest)
```
