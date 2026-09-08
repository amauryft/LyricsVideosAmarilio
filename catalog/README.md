# The catalog

Everything about a release — its art, its audio, its lyrics, its brand and
its renders — lives in one folder, and every release folder has the same
shape. Producing the next one is therefore the same set of steps as the
last one, and nothing has to be looked up in a script.

```
catalog/
  albums/<slug>/      full albums (Peregrino, Vasos de Barro)
  eps/<slug>/         3-track EPs
  singles/<slug>/     one-track singles
  contact-sheets/     SHEET-thumbnails.png, SHEET-lyrics.png (whole catalog)
  references/         lyrics documents that span several releases
  extra-fonts.txt     fonts the SessionStart hook keeps installed
```

## A release folder

```
catalog/<albums|eps|singles>/<release-slug>/
  release.json              the manifest: type, title, artist, track list
  brand.json                visual identity; its paths resolve from here
  README.md                 optional per-release notes
  assets/
    graphics/               cover + background — what brand.json points at
    music/                  source audio, NN-<track-slug>.<ext>
    references/             official lyrics (PDF/txt), layout studies
  lyrics/
    <track-slug>.lrc        timed lyrics — what gets rendered
    <track-slug>.raw.lrc    raw transcription, timing anchors only
  renders/
    <track-slug>.mp4        full-size render (never committed)
    <track-slug>-thumb.png  intro slide / YouTube thumbnail
    <track-slug>-lyrics.png a lyric frame, for reference
```

The **track slug is the key**: audio, lyrics, render and stills are all
named from it, so only `release.json` has to be edited when a track is
added, and only for its number, title and audio file.

## release.json

```json
{
  "slug": "peregrino",
  "type": "album",
  "title": "Peregrino",
  "artist": "Amarílio Fontenele",
  "disc": "CD2",
  "brand": "brand.json",
  "notes": "anything the next session should know",
  "tracks": [
    {"n": 1, "slug": "ah-voce", "title": "Ah Você!",
     "audio": "assets/music/01-ah-voce.mp3"}
  ]
}
```

`brand` is `null` until the release has artwork and a brand config — that
is how a staged-but-not-yet-produced release (currently *Vasos de Barro*)
is distinguished from a finished one.

## Starting a release

```bash
# Scaffolds the folders and the manifest, and imports the audio under the
# naming convention (accents and ALL CAPS in the source names are handled).
python3 tools/new_release.py --type album --title "Vasos de Barro" --disc CD1 \
    --audio ~/Downloads/CD1/*.mp3
```

Then drop `cover`/`bg` into `assets/graphics/`, write `brand.json` beside
`release.json` pointing at them with paths like `assets/graphics/cover.png`,
and set `"brand": "brand.json"`. The renderer, `tools/make_thumbs.py` and
the font-installing SessionStart hook all discover the release from there
with no further edits.

`python3 -m unittest discover -s tests` checks every manifest against what
is actually on disk, so a typo in a path fails the suite rather than a
render three steps later.

## What is and is not committed

Source audio under `assets/music/` **is** committed: cloud sessions are
ephemeral, so git is the only copy that survives one. Rendered video under
`renders/` is **not** — Google Drive is the archive (see the delivery rules
in the root `README.md`). The stills beside it are committed.
