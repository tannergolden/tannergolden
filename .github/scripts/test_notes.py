# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The Field Notes: the library, the weekly draw, and every open data source, all offline.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

The sources are read from fixtures shaped like each one's real response, with
made-up identifiers, so nothing here touches the network.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import random
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("notes", HERE / "notes.py")
notes = importlib.util.module_from_spec(spec)
sys.modules["notes"] = notes  # dataclasses look their module up while the class is built
spec.loader.exec_module(notes)
LIBRARY = HERE.parent / "notes"
TODAY = dt.date(2026, 9, 26)

RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Example feature is generally available</title><link>https://github.blog/changelog/2026-09-24-example/</link>
<pubDate>Thu, 24 Sep 2026 17:00:00 +0000</pubDate></item>
<item><title>An old change</title><link>https://github.blog/changelog/2026-08-01-old/</link>
<pubDate>Sat, 01 Aug 2026 17:00:00 +0000</pubDate></item></channel></rss>"""
EOL_PYTHON = json.dumps([
    {"cycle": "3.99", "eol": "2031-10-31"},
    {"cycle": "3.10", "eol": "2026-10-31"},
    {"cycle": "3.8", "eol": "2024-10-07"},
]).encode()
ADVISORIES = json.dumps([
    {"ghsa_id": "GHSA-0000-0000-0000", "summary": "Example package lets a crafted path escape its directory",
     "html_url": "https://github.com/advisories/GHSA-0000-0000-0000", "published_at": "2026-09-23T10:00:00Z",
     "vulnerabilities": [{"package": {"ecosystem": "npm", "name": "example-package"},
                          "vulnerable_version_range": "< 2.0.1", "first_patched_version": "2.0.1"}]},
    {"ghsa_id": "GHSA-1111-1111-1111", "summary": "Too old to draw", "html_url": "https://github.com/advisories/GHSA-1111-1111-1111",
     "published_at": "2026-08-01T10:00:00Z", "vulnerabilities": [{"package": {"ecosystem": "pip", "name": "old"}}]},
]).encode()
KEV = json.dumps({"vulnerabilities": [
    {"cveID": "CVE-0000-00001", "vendorProject": "Example", "product": "Gateway",
     "vulnerabilityName": "Example Gateway Authentication Bypass", "dateAdded": "2026-09-22",
     "requiredAction": "Apply mitigations per vendor instructions or discontinue use of the product."},
    {"cveID": "CVE-0000-00002", "vendorProject": "Old", "product": "Thing", "vulnerabilityName": "Old",
     "dateAdded": "2026-01-01", "requiredAction": "Patch."},
]}).encode()
TLDR_TAR = """# tar

> Archiving utility.

- [c]reate a g[z]ipped archive and write it to a [f]ile:

`tar czf {{path/to/target.tar.gz}} {{path/to/file1 path/to/file2 ...}}`

- E[x]tract an archive into the target directory:

`tar xf {{path/to/source.tar}} {{[-C|--directory]}} {{path/to/directory}}`
"""


def fixtures(url: str, headers: dict) -> bytes:
    if url == notes.CHANGELOG:
        return RSS
    if url == notes.EOL.format(product="python"):
        return EOL_PYTHON
    if url.startswith("https://endoflife.date/"):
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    if url.startswith("https://api.github.com/advisories"):
        return ADVISORIES if "severity=high" in url else b"[]"
    if url == notes.KEV:
        return KEV
    raise AssertionError(f"unexpected fetch {url}")


def offline(url: str, headers: dict) -> bytes:
    raise urllib.error.URLError("network unreachable")


class Library(unittest.TestCase):
    def test_a_thousand_notes_per_kind_two_hundred_fifty_per_level(self):
        library = notes.load_library(LIBRARY)
        for kind in notes.KINDS:
            self.assertEqual(len(library[kind]), 1000, kind)
            for level in notes.LEVELS:
                self.assertEqual(sum(n["level"] == level for n in library[kind]), 250, f"{kind}/{level}")

    def test_no_two_notes_of_a_kind_say_the_same_thing(self):
        library = notes.load_library(LIBRARY)
        for kind, pool in library.items():
            texts = [" ".join(n["text"].lower().split()) for n in pool]
            self.assertEqual(len(texts), len(set(texts)), kind)

    def test_a_banned_dash_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            for kind in notes.KINDS:
                body = "".join(f'[[note]]\nlevel = "{lv}"\ntopic = "Git"\ntext = "fine."\n\n' for lv in notes.LEVELS)
                if kind == "tip":
                    body += '[[note]]\nlevel = "beginner"\ntopic = "Git"\ntext = "one \u2014 two."\n'
                Path(d, f"{kind}.toml").write_text(body, encoding="utf-8")
            with self.assertRaises(SystemExit) as caught:
                notes.load_library(Path(d))
            self.assertIn("em dash", str(caught.exception))


class Draw(unittest.TestCase):
    def setUp(self):
        self.library = notes.load_library(LIBRARY)

    def test_a_curated_week_has_every_kind_in_githubs_order_and_every_level(self):
        for day in (TODAY + dt.timedelta(weeks=w) for w in range(40)):
            alerts = notes.choose(self.library, day, None)
            self.assertEqual([a.kind for a in alerts], list(notes.KINDS))
            self.assertEqual({a.label.split(" · ")[0].lower() for a in alerts}, set(notes.LEVELS))

    def test_the_same_week_draws_the_same_block(self):
        monday, sunday = dt.date(2026, 9, 21), dt.date(2026, 9, 27)
        a = notes.block(notes.choose(self.library, monday, None), self.library, monday)
        b = notes.block(notes.choose(self.library, sunday, None), self.library, sunday)
        self.assertEqual(a, b)

    def test_a_pool_does_not_repeat_until_it_has_all_been_shown(self):
        pool_weeks = [TODAY + dt.timedelta(weeks=4 * i) for i in range(250)]
        texts = [notes.curated(self.library, "tip", notes.week_of(d)).text for d in pool_weeks]
        self.assertEqual(len(set(texts)), 250)

    def test_about_half_the_alerts_come_from_open_data(self):
        weeks = [notes.week_of(TODAY) + w for w in range(400)]
        share = sum(notes.coin(w, k).random() < notes.OPEN_SHARE for w in weeks for k in notes.KINDS) / (400 * 5)
        self.assertTrue(0.45 < share < 0.55, share)

    def test_every_source_draws_its_alert(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "tar.md").write_text(TLDR_TAR, encoding="utf-8")
            alerts = notes.choose(self.library, TODAY, fixtures, share=1.0, tldr_dir=Path(d))
        by_kind = {a.kind: a for a in alerts}
        self.assertIn("Example feature is generally available", by_kind["note"].text)
        self.assertRegex(by_kind["tip"].text, r"^(Create a gzipped archive and write it to a file: `tar czf <path/to/target\.tar\.gz>|"
                                              r"Extract an archive into the target directory: `tar xf <path/to/source\.tar> --directory)")
        self.assertIn("Python 3.10 stops getting security fixes on 31 October 2026", by_kind["important"].text)
        self.assertIn("Move to 3.99", by_kind["important"].text)
        self.assertIn("`example-package`", by_kind["warning"].text)
        self.assertIn("Update to `2.0.1` or later.", by_kind["warning"].text)
        self.assertIn("CVE-0000-00001", by_kind["caution"].label)
        self.assertEqual([a.source for a in alerts], ["GitHub changelog", "tldr-pages (CC BY 4.0)", "endoflife.date",
                                                      "GitHub Advisory Database (CC BY 4.0)", "CISA KEV"])

    def test_a_source_that_is_down_hands_its_alert_to_the_library(self):
        alerts = notes.choose(self.library, TODAY, offline, share=1.0)
        self.assertEqual([a.source for a in alerts], [""] * 5)
        self.assertEqual([a.kind for a in alerts], list(notes.KINDS))

    def test_open_data_is_made_safe(self):
        self.assertEqual(notes.plain("a \u2014 b \u2013 c"), "a - b - c")
        self.assertEqual(notes.plain("<b>x</b> *y* [z]"), "x \\*y\\* \\[z\\]")
        self.assertTrue(notes.plain("word " * 100, 40).endswith("…"))

    def test_the_block_credits_the_open_data_it_used(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "tar.md").write_text(TLDR_TAR, encoding="utf-8")
            alerts = notes.choose(self.library, TODAY, fixtures, share=1.0, tldr_dir=Path(d))
        out = notes.block(alerts, self.library, TODAY)
        self.assertIn("Open data this week: GitHub changelog, tldr-pages (CC BY 4.0)", out)
        self.assertIn("5,000 curated notes", out)
        for kind in notes.KINDS:
            self.assertIn(f"> [!{kind.upper()}]", out)


class Eastern(unittest.TestCase):
    """Every day an alert shows, and every week it counts, is the day in EST (UTC-5), whatever the season."""

    def test_a_change_shipped_late_at_night_in_utc_is_dated_the_day_before(self):
        rss = RSS.replace(b"Thu, 24 Sep 2026 17:00:00 +0000", b"Fri, 25 Sep 2026 03:00:00 +0000")

        def fetch(url: str, headers: dict) -> bytes:
            return rss
        self.assertEqual(notes.changelog(random.Random(0), TODAY, fetch).label, "GitHub changelog · 24 Sep")

    def test_an_advisory_is_this_weeks_by_its_day_in_est(self):
        def at(stamp: str):
            data = ADVISORIES.replace(b'"2026-09-23T10:00:00Z"', f'"{stamp}"'.encode())

            def fetch(url: str, headers: dict) -> bytes:
                return data if "severity=high" in url else b"[]"
            return notes.advisory(random.Random(0), TODAY, fetch)
        # 02:00 UTC on the 19th is still the 18th in EST, eight days before the 26th; 06:00 UTC is the 19th.
        self.assertIsNone(at("2026-09-19T02:00:00Z"))
        self.assertIsNotNone(at("2026-09-19T06:00:00Z"))


class Readme(unittest.TestCase):
    def test_only_the_block_moves(self):
        text = f"# Title\n\n{notes.START}\nold\n{notes.END}\n\nfooter\n"
        out = notes.apply(text, f"{notes.START}\nnew\n{notes.END}")
        self.assertEqual(out, f"# Title\n\n{notes.START}\nnew\n{notes.END}\n\nfooter\n")

    def test_missing_markers_fail_loudly(self):
        with self.assertRaises(SystemExit):
            notes.apply("# Title\n", "block")


if __name__ == "__main__":
    unittest.main()
