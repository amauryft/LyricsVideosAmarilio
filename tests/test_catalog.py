"""The catalog manifests must keep matching what is on disk."""

import unittest
from pathlib import Path

from lyricsvideo.brand import load_brand
from lyricsvideo.catalog import (
    TYPE_DIRS,
    CatalogError,
    find_track,
    load_catalog,
    load_release,
)
from lyricsvideo.lrc import parse_lrc

CATALOG = Path(__file__).resolve().parent.parent / "catalog"

# Delivered before the catalog layout existed; their .lrc was never
# committed and is gone with the container that produced it.
KNOWN_MISSING_LYRICS = {"como-voce-esta", "louvor-com-frevor"}


class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.releases = load_catalog(CATALOG)

    def test_every_release_folder_has_a_manifest(self):
        found = {
            d
            for group in TYPE_DIRS.values()
            for d in (CATALOG / group).iterdir()
            if d.is_dir()
        }
        loaded = {r.directory for r in self.releases}
        self.assertEqual(found, loaded)

    def test_release_slugs_are_unique(self):
        slugs = [r.slug for r in self.releases]
        self.assertEqual(len(slugs), len(set(slugs)))

    def test_track_slugs_are_unique_across_the_catalog(self):
        slugs = [t.slug for r in self.releases for t in r.tracks]
        self.assertEqual(len(slugs), len(set(slugs)), "track slugs name renders")

    def test_tracks_are_numbered_from_one_without_gaps(self):
        for release in self.releases:
            with self.subTest(release=release.slug):
                self.assertEqual(
                    [t.n for t in release.tracks], list(range(1, len(release.tracks) + 1))
                )

    def test_declared_files_exist(self):
        problems = [p for r in self.releases for p in r.problems()]
        self.assertEqual(problems, [])

    def test_brands_load_and_their_graphics_resolve(self):
        for release in self.releases:
            if release.brand is None:
                continue
            with self.subTest(release=release.slug):
                brand = load_brand(release.brand)  # raises if cover/bg are missing
                self.assertTrue(brand.background.is_file())
                self.assertTrue(brand.cover.is_file())
                self.assertEqual(brand.background.parent, release.graphics)

    def test_timed_lyrics_parse(self):
        for release in self.releases:
            for track in release.tracks:
                if not track.lyrics.is_file():
                    continue
                with self.subTest(track=track.slug):
                    lyrics = parse_lrc(track.lyrics.read_text(encoding="utf-8"))
                    self.assertTrue(lyrics.lines, "no timed lines")

    def test_produced_tracks_have_a_thumbnail(self):
        """A release with a brand is in production: its stills are committed."""
        for release in self.releases:
            if release.brand is None:
                continue
            for track in release.tracks:
                with self.subTest(track=track.slug):
                    self.assertTrue(track.thumb.is_file(), track.thumb)

    def test_no_new_track_loses_its_timed_lyrics(self):
        """Rendered songs keep their .lrc — it is the only copy there is.

        KNOWN_MISSING_LYRICS are two singles delivered before the catalog
        layout existed, whose .lrc never got committed; they have to be
        transcribed again. Nothing may join them.
        """
        missing = {
            track.slug
            for release in self.releases
            if release.brand is not None
            for track in release.tracks
            if not track.lyrics.is_file()
        }
        self.assertEqual(missing - KNOWN_MISSING_LYRICS, set())

    def test_find_track_locates_a_track_by_slug(self):
        release, track = find_track("nicodemos", CATALOG)
        self.assertEqual(release.slug, "peregrino")
        self.assertEqual(track.n, 9)
        self.assertEqual(track.audio.name, "09-nicodemos.mp3")

    def test_find_track_rejects_an_unknown_slug(self):
        with self.assertRaises(CatalogError):
            find_track("no-such-song", CATALOG)

    def test_load_release_rejects_a_folder_without_a_manifest(self):
        with self.assertRaises(CatalogError):
            load_release(CATALOG)


if __name__ == "__main__":
    unittest.main()
