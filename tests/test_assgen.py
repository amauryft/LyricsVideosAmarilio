import unittest

from lyricsvideo.assgen import _ass_color, _ass_time, build_ass
from lyricsvideo.lrc import parse_lrc
from lyricsvideo.themes import get_theme


class AssGenTest(unittest.TestCase):
    def test_color_conversion(self):
        self.assertEqual(_ass_color("#ff8000"), "&H000080FF")
        self.assertEqual(_ass_color("#000000", 128), "&H80000000")

    def test_time_format(self):
        self.assertEqual(_ass_time(0), "0:00:00.00")
        self.assertEqual(_ass_time(65.25), "0:01:05.25")
        self.assertEqual(_ass_time(3661.5), "1:01:01.50")

    def test_build_ass_contains_lines_and_title_card(self):
        lyrics = parse_lrc(
            "[ti:Song]\n[ar:Artist]\n[00:05.00]hello world\n[00:08.00]second line\n"
        )
        doc = build_ass(lyrics, get_theme("midnight"), 1920, 1080)
        self.assertIn("PlayResX: 1920", doc)
        self.assertIn("hello world", doc)
        self.assertIn("Style: Current", doc)
        self.assertIn("TitleCard", doc)  # lyrics start late enough for a card
        self.assertIn("Song", doc)
        self.assertIn("Artist", doc)

    def test_no_title_card_when_lyrics_start_immediately(self):
        lyrics = parse_lrc("[ti:Song]\n[00:00.50]instant\n")
        doc = build_ass(lyrics, get_theme("neon"), 1280, 720)
        self.assertNotIn("TitleCard,,", doc.split("[Events]")[1])

    def test_braces_are_neutralized(self):
        lyrics = parse_lrc("[00:01.00]weird {\\b1} text\n")
        doc = build_ass(lyrics, get_theme("minimal"), 1280, 720)
        self.assertNotIn("{\\b1}", doc)


if __name__ == "__main__":
    unittest.main()
