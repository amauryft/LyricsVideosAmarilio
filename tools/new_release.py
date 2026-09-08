#!/usr/bin/env python3
"""Scaffold a new release folder in the catalog.

Creates catalog/<albums|eps|singles>/<slug>/ with the standard subfolders
and a release.json, and — with --audio — imports the source files under the
catalog's naming convention, so the decomposed-Unicode originals stop being
something anyone has to glob around.

    # Tracks named by hand
    python3 tools/new_release.py --type single --title "Nova Canção" \
        --track "nova-cancao=Nova Canção"

    # Tracks read from the delivered audio ("NN TÍTULO.mp3" -> 03-titulo.mp3)
    python3 tools/new_release.py --type album --title "Vasos de Barro" \
        --disc CD1 --audio "~/Downloads/CD1/"*.mp3

Then drop cover/background into assets/graphics/, write brand.json beside
release.json pointing at them, and the render and thumbnail tooling picks
the release up with no further edits.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lyricsvideo.catalog import TYPE_DIRS, load_catalog  # noqa: E402

ARTIST = "Amarílio Fontenele"
SUBDIRS = ("assets/graphics", "assets/music", "assets/references", "lyrics", "renders")


def slugify(text: str) -> str:
    """'04 PELO CHÃO' -> 'pelo-chao' — the slug every other path is built on."""
    plain = unicodedata.normalize("NFKD", text)
    plain = "".join(c for c in plain if not unicodedata.combining(c))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", plain.lower())).strip("-")


def track_from_audio(path: Path, fallback_n: int) -> dict:
    """Read 'NN Title.ext' into a manifest entry plus its source path."""
    stem = unicodedata.normalize("NFC", path.stem).strip()
    match = re.match(r"^(\d{1,2})\s*[-.]?\s+(.*)$", stem)
    n, title = (int(match.group(1)), match.group(2)) if match else (fallback_n, stem)
    title = title.strip()
    return {
        "n": n,
        "slug": slugify(title),
        "title": title if not title.isupper() else title.title(),
        "source": path,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--type", required=True, choices=sorted(TYPE_DIRS),
                   help="album, ep or single")
    p.add_argument("--title", required=True, help="Release title")
    p.add_argument("--slug", help="Folder name (default: slugified title)")
    p.add_argument("--artist", default=ARTIST)
    p.add_argument("--disc", help="Disc label, e.g. CD1")
    p.add_argument("--notes", help="Anything the next session should know")
    p.add_argument("--track", action="append", default=[], metavar="SLUG=TITLE",
                   help="Track without audio yet; repeatable")
    p.add_argument("--audio", action="append", default=[], type=Path, metavar="FILE",
                   help="Source audio to import as NN-<slug>.<ext>; repeatable")
    p.add_argument("--copy", action="store_true",
                   help="Copy the --audio files instead of moving them")
    args = p.parse_args()

    slug = args.slug or slugify(args.title)
    base = ROOT / "catalog" / TYPE_DIRS[args.type] / slug
    if (base / "release.json").exists():
        print(f"error: {base.relative_to(ROOT)} already exists", file=sys.stderr)
        return 2

    tracks = []
    for i, spec in enumerate(args.track, start=1):
        if "=" not in spec:
            print(f"error: --track wants SLUG=TITLE, got {spec!r}", file=sys.stderr)
            return 2
        t_slug, t_title = spec.split("=", 1)
        tracks.append({"n": i, "slug": t_slug.strip(), "title": t_title.strip(),
                       "source": None})
    for i, path in enumerate(args.audio, start=len(tracks) + 1):
        path = path.expanduser()
        if not path.is_file():
            print(f"error: no such audio file: {path}", file=sys.stderr)
            return 2
        tracks.append(track_from_audio(path, i))

    tracks.sort(key=lambda t: t["n"])
    for i, track in enumerate(tracks, start=1):
        track["n"] = i
    if len({t["slug"] for t in tracks}) != len(tracks):
        print("error: duplicate track slugs", file=sys.stderr)
        return 2

    for sub in SUBDIRS:
        (base / sub).mkdir(parents=True, exist_ok=True)

    entries = []
    for track in tracks:
        source = track["source"]
        ext = source.suffix.lower() if source else ".mp3"
        rel = f"assets/music/{track['n']:02d}-{track['slug']}{ext}"
        if source:
            (shutil.copy2 if args.copy else shutil.move)(str(source), base / rel)
        entries.append({"n": track["n"], "slug": track["slug"],
                        "title": track["title"], "audio": rel})

    manifest = {"slug": slug, "type": args.type, "title": args.title,
                "artist": args.artist}
    if args.disc:
        manifest["disc"] = args.disc
    manifest["brand"] = None
    if args.notes:
        manifest["notes"] = args.notes
    manifest["tracks"] = entries
    (base / "release.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Created {base.relative_to(ROOT)} with {len(entries)} track(s)")
    print("Next:")
    print(f"  1. cover + background -> {base.relative_to(ROOT)}/assets/graphics/")
    print(f"  2. official lyrics    -> {base.relative_to(ROOT)}/assets/references/")
    print(f"  3. write {base.relative_to(ROOT)}/brand.json (paths relative to it,")
    print('     e.g. "cover": "assets/graphics/cover.png"), then set')
    print('     "brand": "brand.json" in release.json')
    print("  4. transcribe each track, then render — see README.md")
    load_catalog()  # fails loudly if the new manifest is inconsistent
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
