import unittest

from lyricsvideo.lrc import parse_lrc


class ParseLrcTest(unittest.TestCase):
    def test_basic_lines_and_metadata(self):
        lyrics = parse_lrc(
            "[ti:My Song]\n[ar:Someone]\n"
            "[00:05.00]first\n[00:10.00]second\n[00:15.00]third\n",
            audio_duration=20.0,
        )
        self.assertEqual(lyrics.title, "My Song")
        self.assertEqual(lyrics.artist, "Someone")
        self.assertEqual([l.text for l in lyrics.lines], ["first", "second", "third"])
        self.assertEqual(lyrics.lines[0].start, 5.0)
        self.assertEqual(lyrics.lines[0].end, 10.0)
        self.assertEqual(lyrics.lines[2].end, 20.0)  # last line runs to audio end

    def test_multiple_time_tags_per_line(self):
        lyrics = parse_lrc("[00:01.00][00:03.00]chorus\n[00:05.00]next\n")
        self.assertEqual([(l.start, l.text) for l in lyrics.lines],
                         [(1.0, "chorus"), (3.0, "chorus"), (5.0, "next")])

    def test_blank_timed_line_ends_previous(self):
        lyrics = parse_lrc("[00:01.00]verse\n[00:04.00]\n[00:08.00]back\n")
        self.assertEqual(len(lyrics.lines), 2)
        self.assertEqual(lyrics.lines[0].end, 4.0)
        self.assertEqual(lyrics.lines[1].start, 8.0)

    def test_offset_shifts_earlier(self):
        lyrics = parse_lrc("[offset:500]\n[00:05.00]hello\n")
        self.assertAlmostEqual(lyrics.lines[0].start, 4.5)

    def test_unsorted_input_is_sorted(self):
        lyrics = parse_lrc("[00:10.00]b\n[00:05.00]a\n")
        self.assertEqual([l.text for l in lyrics.lines], ["a", "b"])

    def test_two_digit_fraction_and_colon_separator(self):
        lyrics = parse_lrc("[00:05.25]x\n[01:02:50]y\n")
        self.assertAlmostEqual(lyrics.lines[0].start, 5.25)
        self.assertAlmostEqual(lyrics.lines[1].start, 62.5)

    def test_minimum_duration_enforced(self):
        lyrics = parse_lrc("[00:05.00]a\n[00:05.10]b\n")
        self.assertGreaterEqual(lyrics.lines[0].end - lyrics.lines[0].start, 0.5)


if __name__ == "__main__":
    unittest.main()
