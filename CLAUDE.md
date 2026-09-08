# Lyrics Videos — session guide

This repo produces YouTube lyrics videos for Amarilio Fontenele's catalog.
The **authoritative standing rules live in `README.md`** under "Project
guide (how this catalog is produced)" and "Per-song workflow (the
pattern)" — read those two sections before doing any catalog work. The
notes below are the operational quick reference.

## Environment (cloud sessions)

A SessionStart hook (`.claude/hooks/session-start.sh`) installs everything
automatically: static ffmpeg/ffprobe, all brand fonts, `pip install -e .`
plus `sherpa-onnx numpy pillow pypdf`, and the offline Whisper models in
`/home/user/models`. Its status summary appears in the session context —
check it before assuming a tool is missing. If something failed, the
README's "Remote sandbox setup" section has the manual recipes (apt and
YouTube are blocked; GitHub release downloads and Google Fonts work).

**Fonts are dynamic**: the hook installs every family referenced by any
`*font*` key in `brands/*.json`, plus every family listed in
`brands/extra-fonts.txt`. To add a font for a future brand, add its Google
Fonts family name to that txt file — no hook changes needed.

## Layouts

A brand's `layout` key selects the look: `"showcase"` (album art +
auto-fitted lyric block — the current standard), `"columns"` (three-column
magazine), or omitted (classic centered). Layouts are implemented in
`lyricsvideo/assgen.py` (geometry constants at the top, one builder
function per layout) with brand keys declared in `lyricsvideo/brand.py`.
A new layout variation = a new builder in `assgen.py` + any new brand keys
in `brand.py`; follow the showcase builder as the template.

## Command cheat sheet

```bash
# Transcribe a new song (Brazilian Portuguese) → songs/<slug>.lrc
python3 -m lyricsvideo transcribe songs/<slug>.mp3 -l pt --title "Título"

# Test render (fast): preview 30s at quarter size
python3 -m lyricsvideo render songs/<slug>.mp3 songs/<slug>.lrc \
    --brand brands/<brand>.json --preview 30 --resolution 960x540 -o /tmp/test.mp4

# Final render (defaults are already YouTube-ready 1080p) — verify with ffprobe
python3 -m lyricsvideo render songs/<slug>.mp3 songs/<slug>.lrc \
    --brand brands/<brand>.json -o videos/<slug>.mp4

# Thumbnails / intro slides (all songs + contact sheet)
python3 tools/make_thumbs.py

# Tests
python3 -m unittest discover -s tests -v
```

## Non-negotiables (full detail in README)

- **Lyrics source of truth**: the official PDFs in `assets/references/`.
  Transcriptions (`songs/*.raw.lrc`) give timing anchors only — but match
  what is actually sung when the recording deviates from the PDF.
- **Anticipation**: lyrics run ~1.5s ahead of the voice (`--lead`), never
  behind.
- **Delivery**: videos are NOT stored in git (`videos/` is gitignored).
  Chat is the primary delivery channel — one compressed file ≤ 30 MiB per
  song, never split ".partNN" files to the user. Masters go to the Google
  Drive folder; the temporary `videos-delivery` branch is a transfer pipe
  only.
- **Output format**: 1920×1080 H.264 yuv420p 30fps + AAC 192k, faststart
  (the renderer's defaults) — `ffprobe` every final render before delivery.
- Work **one video at a time**; iterate with `--preview` before any full
  encode.

## Catalog state (update this when it changes)

- 16-song catalog (4 EPs × 3 + 4 singles): rendered and delivered
  2026-09-05.
- *Peregrino* album (CD2, 13 tracks): rendered and delivered 2026-09-08.
- *Vasos de Barro* (CD1): sources being staged — root MP3s
  ("NN TÍTULO.mp3", decomposed Unicode: address with shell globs), lyrics
  PDF `CD1 - VASOS DE BARRO asLetras.pdf`, artwork
  `Vasos de barro BG framed.png` / `vasos teh barro cover.png`. No brand
  JSON or `.lrc` files yet.
