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
`*font*` key in `catalog/*/*/brand.json`, plus every family listed in
`catalog/extra-fonts.txt`. To add a font for a future brand, add its Google
Fonts family name to that txt file — no hook changes needed.

## Where things live

Everything about a release is in one folder, always the same shape:

```
catalog/<albums|eps|singles>/<release>/
  release.json  brand.json
  assets/graphics/   cover.png, bg.png        (what brand.json points at)
  assets/music/      NN-<slug>.mp3            (source audio, committed)
  assets/references/ official lyrics PDF/txt
  lyrics/            <slug>.lrc, <slug>.raw.lrc
  renders/           <slug>.mp4 (gitignored), <slug>-thumb.png
```

`catalog/README.md` is the authority on the layout and the `release.json`
format. `lyricsvideo/catalog.py` reads the manifests
(`load_catalog()`, `find_track(slug)`); the tooling discovers releases
through it, so adding one needs no script edits. Start a release with
`python3 tools/new_release.py` — never by hand.

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
# R is the release folder, e.g. catalog/albums/peregrino
R=catalog/<albums|eps|singles>/<release>

# Transcribe a new song (Brazilian Portuguese)
python3 -m lyricsvideo transcribe $R/assets/music/NN-<slug>.mp3 \
    -l pt --title "Título" -o $R/lyrics/<slug>.raw.lrc

# Test render (fast): preview 30s at quarter size
python3 -m lyricsvideo render $R/assets/music/NN-<slug>.mp3 $R/lyrics/<slug>.lrc \
    --brand $R/brand.json --preview 30 --resolution 960x540 -o /tmp/test.mp4

# Final render (defaults are already YouTube-ready 1080p) — verify with ffprobe
python3 -m lyricsvideo render $R/assets/music/NN-<slug>.mp3 $R/lyrics/<slug>.lrc \
    --brand $R/brand.json -o $R/renders/<slug>.mp4

# Thumbnails / intro slides (all songs + contact sheet)
python3 tools/make_thumbs.py

# Scaffold a new release (folders + manifest + audio import)
python3 tools/new_release.py --type album --title "Título" --audio ~/audio/*.mp3

# Tests — these also check every manifest against what is on disk
python3 -m unittest discover -s tests -v
```

## Non-negotiables (full detail in README)

- **Lyrics source of truth**: the official PDFs — the release's own
  `assets/references/`, or `catalog/references/` for the ones spanning
  several releases. Transcriptions (`lyrics/<slug>.raw.lrc`) give timing
  anchors only — but match what is actually sung when the recording
  deviates from the PDF.
- **Anticipation**: lyrics run ~1.5s ahead of the voice (`--lead`), never
  behind.
- **Delivery**: videos are NOT stored in git (`<release>/renders/*.mp4`
  is gitignored; the stills beside it are committed, and the source audio
  in `assets/music/` is committed on purpose — git is the only copy that
  survives an ephemeral session). Chat is the primary delivery channel — one compressed file ≤ 30 MiB per
  song, never split ".partNN" files to the user. Masters go to the Google
  Drive folder; the temporary `videos-delivery` branch is a transfer pipe
  only.
- **Output format**: 1920×1080 H.264 yuv420p 30fps + AAC 192k, faststart
  (the renderer's defaults) — `ffprobe` every final render before delivery.
- Work **one video at a time**; iterate with `--preview` before any full
  encode.

## Catalog state (update this when it changes)

- **2026-09-08 — the repo was reorganized into `catalog/`** (10 release
  folders, 40 tracks). Old paths (`songs/`, `brands/`, `compositions/`,
  `videos/`, `assets/albums/`) are gone.
- 16-song catalog (4 EPs × 3 + 4 singles): rendered and delivered
  2026-09-05. Two of them, `como-voce-esta` and `louvor-com-frevor`, have
  **no `.lrc` in the repo** — it was never committed and is lost; they
  need re-transcribing if those videos are ever re-rendered.
- *Peregrino* album (CD2, 13 tracks): rendered and delivered 2026-09-08 —
  `catalog/albums/peregrino/`.
- *Vasos de Barro* (CD1, 11 tracks): staged in
  `catalog/albums/vasos-de-barro/` — audio and lyrics PDF in place,
  artwork in `assets/graphics/`. No brand JSON or `.lrc` files yet, so its
  manifest carries `"brand": null`. Track titles there came from the
  source filenames; confirm against the PDF when staging lyrics.
