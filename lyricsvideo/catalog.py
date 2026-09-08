"""The catalog: releases (albums, EPs, singles) and the tracks in them.

Every release lives in one self-contained folder, the same shape whatever
its type, so producing a new one is the same set of steps every time:

    catalog/<albums|eps|singles>/<release-slug>/
        release.json          this manifest: type, title, artist, tracks
        brand.json            visual identity; its paths resolve from here
        assets/graphics/      cover + background the brand points at
        assets/music/         source audio, NN-<track-slug>.<ext>
        assets/references/    official lyrics (PDF/txt) and layout studies
        lyrics/               <track-slug>.lrc and <track-slug>.raw.lrc
        renders/              <track-slug>.mp4 and its -thumb/-lyrics stills

A manifest names the tracks and where their audio sits; everything else is
found by convention from the track slug, so the only thing to write by hand
when a release grows a track is one entry in `tracks`.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

# release type -> the directory that groups releases of that type
TYPE_DIRS = {"album": "albums", "ep": "eps", "single": "singles"}


class CatalogError(Exception):
    """A release manifest is missing, malformed or inconsistent."""


def catalog_root() -> Path:
    """The catalog directory: $LYRICSVIDEO_CATALOG, else the repo's own."""
    env = os.environ.get("LYRICSVIDEO_CATALOG")
    if env:
        return Path(env).resolve()
    return (Path(__file__).resolve().parent.parent / "catalog").resolve()


@dataclass(frozen=True)
class Track:
    n: int
    slug: str
    title: str
    directory: Path  # the release folder this track belongs to
    audio: Path

    @property
    def lyrics(self) -> Path:
        """Timed lyrics — the file rendered into the video."""
        return self.directory / "lyrics" / f"{self.slug}.lrc"

    @property
    def raw_lyrics(self) -> Path:
        """Raw transcription kept as timing anchors only."""
        return self.directory / "lyrics" / f"{self.slug}.raw.lrc"

    @property
    def render(self) -> Path:
        return self.directory / "renders" / f"{self.slug}.mp4"

    @property
    def thumb(self) -> Path:
        return self.directory / "renders" / f"{self.slug}-thumb.png"

    @property
    def lyrics_still(self) -> Path:
        return self.directory / "renders" / f"{self.slug}-lyrics.png"


@dataclass(frozen=True)
class Release:
    slug: str
    type: str
    title: str
    artist: str
    directory: Path
    tracks: tuple[Track, ...]
    brand: Path | None = None
    disc: str | None = None
    notes: str | None = None

    @property
    def graphics(self) -> Path:
        return self.directory / "assets" / "graphics"

    @property
    def music(self) -> Path:
        return self.directory / "assets" / "music"

    @property
    def references(self) -> Path:
        return self.directory / "assets" / "references"

    @property
    def renders(self) -> Path:
        return self.directory / "renders"

    def track(self, slug: str) -> Track:
        for track in self.tracks:
            if track.slug == slug:
                return track
        raise CatalogError(f"No track {slug!r} in release {self.slug!r}")

    def problems(self) -> list[str]:
        """Everything the manifest promises that is not actually on disk."""
        issues = []
        if self.brand is not None and not self.brand.is_file():
            issues.append(f"{self.slug}: missing brand {self.brand.name}")
        for track in self.tracks:
            if not track.audio.is_file():
                issues.append(
                    f"{self.slug}/{track.slug}: missing audio "
                    f"{track.audio.relative_to(self.directory)}"
                )
        return issues


def load_release(path: str | Path) -> Release:
    """Load one release from its folder (or directly from its release.json)."""
    path = Path(path)
    manifest = path if path.is_file() else path / "release.json"
    if not manifest.is_file():
        raise CatalogError(f"No release.json in {path}")
    directory = manifest.parent

    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Invalid JSON in {manifest}: {exc}") from exc

    missing = {"slug", "type", "title", "tracks"} - set(data)
    if missing:
        raise CatalogError(f"{manifest}: missing key(s) {', '.join(sorted(missing))}")
    if data["type"] not in TYPE_DIRS:
        raise CatalogError(
            f"{manifest}: type {data['type']!r} is not one of "
            f"{', '.join(sorted(TYPE_DIRS))}"
        )

    tracks: list[Track] = []
    seen: set[str] = set()
    for entry in data["tracks"]:
        slug = entry["slug"]
        if slug in seen:
            raise CatalogError(f"{manifest}: duplicate track slug {slug!r}")
        seen.add(slug)
        tracks.append(
            Track(
                n=int(entry["n"]),
                slug=slug,
                title=entry["title"],
                directory=directory,
                audio=directory / entry["audio"],
            )
        )

    brand = data.get("brand")
    return Release(
        slug=data["slug"],
        type=data["type"],
        title=data["title"],
        artist=data.get("artist", ""),
        directory=directory,
        tracks=tuple(sorted(tracks, key=lambda t: t.n)),
        brand=(directory / brand) if brand else None,
        disc=data.get("disc"),
        notes=data.get("notes"),
    )


def load_catalog(root: str | Path | None = None) -> list[Release]:
    """Every release, ordered albums → EPs → singles, then by slug."""
    root = Path(root) if root is not None else catalog_root()
    releases = []
    for type_name, dir_name in TYPE_DIRS.items():
        for manifest in sorted((root / dir_name).glob("*/release.json")):
            release = load_release(manifest)
            if release.type != type_name:
                raise CatalogError(
                    f"{manifest}: type {release.type!r} does not match its "
                    f"{dir_name}/ location"
                )
            if release.slug != manifest.parent.name:
                raise CatalogError(
                    f"{manifest}: slug {release.slug!r} does not match its "
                    f"folder {manifest.parent.name!r}"
                )
            releases.append(release)
    return releases


def iter_tracks(root: str | Path | None = None):
    """(release, track) for every track in the catalog, in catalog order."""
    for release in load_catalog(root):
        for track in release.tracks:
            yield release, track


def find_track(slug: str, root: str | Path | None = None) -> tuple[Release, Track]:
    """Locate a track by slug, whichever release it belongs to."""
    for release, track in iter_tracks(root):
        if track.slug == slug:
            return release, track
    raise CatalogError(f"No track {slug!r} in the catalog")
