# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""What the four games share with the page: its days, and the settings' regions each run writes its elements into.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import page

SETTINGS = """# The page's settings.
timezone: EST

# The drawings in the README's body.
elements:
  how-it-fits:
    kind: schematic
  # The game.
  # chess:start
  chess:
    kind: "chess"
  # chess:end

# The trophies.
trophies:
  style: trophy
"""


class Days(unittest.TestCase):
    def test_the_page_tells_time_in_est(self):
        moment = page.parse("2026-10-13T03:30:00Z")
        self.assertEqual((page.day(moment), page.until(moment), page.stamp(moment)),
                         ("12 Oct", "12 Oct, 22:30 EST", "2026-10-13T03:30:00Z"))
        self.assertEqual(page.date(page.parse("2027-01-01T02:00:00Z")), "31 Dec 2026", "the year the page's day is in")

    def test_a_note_takes_the_sentences_that_fit(self):
        said = page.sentences([("One.", True), ("x" * 392, False), ("Two.", True), ("Three.", False)])
        self.assertEqual(said, "One. Two. Three.", "a sentence that may be said is left out when it won't fit")
        said = page.sentences([("One.", True), ("x" * 390, False), ("Two.", True), ("Three.", False)])
        self.assertEqual(len(said), 400, "one that fits beside every sentence still to come is said")


class Regions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.settings = Path(self.temp.name) / "markdown.yaml"
        self.settings.write_text(SETTINGS, encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_a_region_is_written_between_its_markers_and_nothing_else_is_touched(self):
        changed = page.set_out(self.settings, {"chess": [("chess", {"kind": "chess", "game": 2})]})
        self.assertEqual(changed, ["chess"])
        text = self.settings.read_text(encoding="utf-8")
        self.assertEqual(text, SETTINGS.replace('  chess:\n    kind: "chess"\n',
                                                '  chess:\n    kind: "chess"\n    game: 2\n'))

    def test_the_regions_are_the_four_games_in_tier_order_then_the_hall(self):
        self.assertEqual(page.REGIONS, ("tictac", "pentago", "checkers", "chess", "hall"))

    def test_a_region_without_its_markers_is_added_at_the_end_of_elements(self):
        changed = page.set_out(self.settings, {"tictac": [("tictac", {"kind": "tictac"})],
                                               "hall": [("hall-of-fame", {"kind": "hall-of-fame", "people": [],
                                                                          "measure": {}})]})
        self.assertEqual(changed, ["tictac", "hall"])
        text = self.settings.read_text(encoding="utf-8")
        self.assertIn('  # chess:end\n  # tictac:start\n  tictac:\n    kind: "tictac"\n  # tictac:end\n'
                      '  # hall:start\n  hall-of-fame:\n    kind: "hall-of-fame"\n    people: []\n    measure: {}\n'
                      '  # hall:end\n\n# The trophies.\ntrophies:\n', text,
                      "after the section's last entry, before the blank line and the comment that open the next")

    def test_a_region_is_written_only_when_it_changed(self):
        regions = {"chess": [("chess", {"kind": "chess", "game": 1})],
                   "hall": [("hall-of-fame", {"kind": "hall-of-fame"})]}
        self.assertEqual(page.set_out(self.settings, regions), ["chess", "hall"])
        before = self.settings.read_text(encoding="utf-8")
        self.assertEqual(page.set_out(self.settings, regions), [], "nothing changed, so nothing is written")
        self.assertEqual(self.settings.read_text(encoding="utf-8"), before)
        regions["hall"] = [("hall-of-fame", {"kind": "hall-of-fame", "people": []})]
        self.assertEqual(page.set_out(self.settings, regions), ["hall"])

    def test_elements_as_the_last_section_take_a_region_at_the_file_s_end(self):
        self.settings.write_text("elements:\n  other:\n    kind: placard\n\n", encoding="utf-8")
        page.set_out(self.settings, {"hall": [("hall-of-fame", {"kind": "hall-of-fame"})]})
        self.assertEqual(self.settings.read_text(encoding="utf-8"),
                         'elements:\n  other:\n    kind: placard\n  # hall:start\n  hall-of-fame:\n'
                         '    kind: "hall-of-fame"\n  # hall:end\n\n')

    def test_markers_out_of_place_and_no_elements_stop_the_run(self):
        for text in ("elements:\n  # chess:end\n  # chess:start\n", "elements:\n  # chess:start\n",
                     "elements:\n  # chess:start\n  # chess:start\n  # chess:end\n", "trophies:\n  style: trophy\n"):
            self.settings.write_text(text, encoding="utf-8")
            with self.subTest(text=text), self.assertRaises(ValueError):
                page.set_out(self.settings, {"chess": [("chess", {"kind": "chess"})]})

    def test_an_element_is_written_a_field_a_line_and_a_list_an_item_a_line(self):
        element = {"kind": "tictac", "places": "house", "result": {"winner": "house", "how": "three boards in a row"},
                   "history": [["G", "e5", "a1", "@octocat"], [1, "Xb8", "Oe6", "@octocat"]],
                   "moves": [["🔳", "Centre", "Xb8", "X", "u"]], "people": [],
                   "leaders": [["tannergolden", 0, 0, [0, 0, 0, 0], 24684994]]}
        self.assertEqual(page.element_yaml("tictac", element).splitlines(), [
            "  tictac:", '    kind: "tictac"', '    places: "house"',
            '    result: {"winner": "house", "how": "three boards in a row"}', "    history:",
            '      - ["G", "e5", "a1", "@octocat"]', '      - [1, "Xb8", "Oe6", "@octocat"]', "    moves:",
            '      - ["🔳", "Centre", "Xb8", "X", "u"]', "    people: []", "    leaders:",
            '      - ["tannergolden", 0, 0, [0, 0, 0, 0], 24684994]'])
        pentago = {"kind": "pentago",
                   "moves": [["⚪", "Edge", "e4", "W", [["ul", "cw", "u"], ["ul", "acw", "v"]]]]}
        self.assertEqual(page.element_yaml("pentago", pentago).splitlines(), [
            "  pentago:", '    kind: "pentago"', "    moves:",
            '      - ["⚪", "Edge", "e4", "W", [["ul", "cw", "u"], ["ul", "acw", "v"]]]'],
            "a hole's turns, each with its link, inline in its row")
        chess = {"kind": "chess", "moves": [{"piece": "pawn", "list": [["🥾", "March!", "e4", "Pawn", "u"]]}]}
        self.assertEqual(page.element_yaml("chess", chess).splitlines(), [
            "  chess:", '    kind: "chess"', "    moves:", '      - piece: "pawn"', "        list:",
            '          - ["🥾", "March!", "e4", "Pawn", "u"]'])
        self.assertTrue(page.element_yaml("chess", chess).endswith("\n"))


if __name__ == "__main__":
    unittest.main()
