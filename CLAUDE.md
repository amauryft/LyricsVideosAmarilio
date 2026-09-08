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

**Three or more weights in one brand**: ASS can only toggle bold, so a
third weight has to be addressed by its own family name — fontconfig
registers named instances like `Crimson Pro SemiBold` and `Crimson Pro
Black`. Google Fonts has no such families (only `Crimson Pro` at weight
600/900), so the hook splits a trailing style word off the name and
fetches the base family at that weight. Just name the instance in the
brand JSON; add `Family:600,900` to `extra-fonts.txt` only for weights no
brand references yet. Verify with `fc-list | grep "<Family>"` — every
weight must appear before rendering, or libass silently substitutes.

## Lyric typography (showcase layout)

Size is **searched, not set**: `build_showcase_ass` finds the largest
size where every row fits the lyric column and every block fits the
band. Three things control it, and none of them is a hardcoded pixel
size:

- **`lines` (brand)** caps a block at that many *rendered rows*, not
  lyric lines — a long line draws as two rows, so counting lines let a
  block reach twice its intended depth and forced the type small.
- **`lyric_max_rows` (brand, default 2)** is the wrap budget: the most
  rows one lyric line may take. This is what really decides how big the
  type can be, since the search grows the size until some line needs an
  extra row.
- **`lyric_scale` (brand)** pushes the size cap. Derive it with
  `python3 tools/lyric_scale.py brands/<brand>.json songs/<album>/*.txt`,
  which prints the maximum for each wrap budget and names the line that
  binds. **It is per-album** — it depends on the typeface's width and on
  that album's longest line, so a value tuned for one font is meaningless
  for another.

Blocks are centred in the band on their own row count, then lifted 10%
(`OPTICAL_LIFT`) because the optical centre sits above the geometric one.

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
- *Vasos de Barro* (CD1, 11 tracks): rendered and delivered 2026-09-08. Lyrics PDF and
  artwork filed (`assets/references/`, `assets/albums/vasos-de-barro/`);
  all 11 songs staged from the PDF and timed (`songs/<slug>.lrc`, with
  the `.spec` files they were generated from). Brand is
  `brands/vasos-de-barro.json` — Crimson Pro throughout: Black title,
  Bold credits, SemiBold Italic lyrics in #DA9864, `lyric_scale` 1.12.
  Recording deviations to keep: track 2 sings an "Ai, meu Deus de toda
  graça" verse the PDF omits, track 3 adds an outro ("o Senhor da
  história"), track 5 closes naming Christ the Lamb of God, track 7 has
  a spoken 2 Coríntios intro plus "Ê ô ê" refrains and a spoken close,
  and track 8 has a spoken bridge.

### Two traps this album exposed

- **Both albums' MP3s share the repo root and the same NN prefixes**
  (CD2/Peregrino titles are ALL CAPS, CD1's are Title Case), so `07
  *.mp3` silently resolves to the wrong album. Resolve audio through
  `songs/vasos-de-barro/tracks.tsv`, and match NFC-normalized — the
  on-disk names are decomposed, so a literal accented path from the
  shell will not match.
- **`showwaves` corrupts non-primary colours** under its default
  `draw=scale` on current ffmpeg builds — the brand-coloured waveform
  rendered green. The renderer now passes `draw=full` and a colour per
  channel (stereo would otherwise fall back to the default palette).
