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



class BlockModeTest(unittest.TestCase):
    def _lyrics(self, spec):
        text = "\n".join(f"[{t}]{s}" for t, s in spec)
        return parse_lrc(text)

    def test_group_blocks_by_size_and_gap(self):
        from lyricsvideo.assgen import group_blocks
        lyrics = self._lyrics([
            ("00:01.00", "a"), ("00:02.00", "b"), ("00:03.00", "c"),
            ("00:04.00", "d"), ("00:05.00", "e"),
        ])
        blocks = group_blocks(lyrics.lines, 4)
        self.assertEqual([len(b) for b in blocks], [4, 1])

        # A blank marker creates a gap that starts a new block early.
        lyrics = self._lyrics([
            ("00:01.00", "a"), ("00:02.00", "b"), ("00:03.00", ""),
            ("00:10.00", "c"), ("00:11.00", "d"),
        ])
        blocks = group_blocks(lyrics.lines, 4)
        self.assertEqual([len(b) for b in blocks], [2, 2])

    def test_block_events_highlight_each_line(self):
        lyrics = self._lyrics([
            ("00:01.00", "one"), ("00:02.00", "two"),
            ("00:03.00", "three"), ("00:04.00", "four"),
        ])
        doc = build_ass(lyrics, get_theme("midnight"), 1920, 1080, block_size=4)
        block_events = [l for l in doc.splitlines() if ",Block," in l]
        self.assertEqual(len(block_events), 4)  # one event per active line
        # Every event shows all four lines stacked.
        for ev in block_events:
            self.assertEqual(ev.count("\\N"), 3)
        # First event fades in, last fades out, middles do neither.
        self.assertIn("\\fad(250,0)", block_events[0])
        self.assertIn("\\fad(0,0)", block_events[1])
        self.assertIn("\\fad(0,250)", block_events[-1])

    def test_single_line_mode_unchanged(self):
        lyrics = self._lyrics([("00:01.00", "solo")])
        doc = build_ass(lyrics, get_theme("midnight"), 1920, 1080, block_size=1)
        self.assertIn(",Current,", doc)
        self.assertNotIn(",Block,", doc)

if __name__ == "__main__":
    unittest.main()
