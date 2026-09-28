# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The latest releases, offline: GitHub's answers come from fixtures.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

The fixtures are shaped like the REST API's responses, with made-up
repositories, so nothing here touches the network.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # releases.py imports placards.py beside it
spec = importlib.util.spec_from_file_location("releases", HERE / "releases.py")
releases = importlib.util.module_from_spec(spec)
sys.modules["releases"] = releases  # dataclasses look their module up while the class is built
spec.loader.exec_module(releases)
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]


def repo(name: str, **extra) -> dict:
    return {"name": name, "full_name": f"me/{name}", "description": f"The {name} kit, drawn as committed SVGs.",
            "language": "Python", "fork": False, "archived": False, "private": False, **extra}


def release(name: str, tag: str, published: str, **extra) -> dict:
    return {"tag_name": tag, "html_url": f"https://github.com/me/{name}/releases/tag/{tag}",
            "published_at": f"{published}T14:20:00Z", "draft": False, "prerelease": False, **extra}


class Fake:
    """Answers the REST API from tables: the repositories, each latest release, and the major tags that exist."""

    def __init__(self, repos: list[dict], latest: dict, majors: set[str] = frozenset(), fail: bool = False):
        self.repos, self.latest, self.majors, self.fail, self.urls = repos, latest, majors, fail, []

    def __call__(self, url: str, headers: dict) -> bytes:
        self.urls.append(url)
        if self.fail:
            raise urllib.error.URLError("unreachable")
        path = url.split("api.github.com", 1)[1].split("?", 1)[0]
        if path == "/users/me/repos":
            return json.dumps(self.repos).encode()
        parts = path.split("/")  # ['', 'repos', 'me', name, ...]
        name = parts[3]
        if path.endswith("/releases/latest") and name in self.latest:
            return json.dumps(self.latest[name]).encode()
        if "/git/ref/tags/" in path and f"{name}@{parts[-1]}" in self.majors:
            return json.dumps({"ref": f"refs/tags/{parts[-1]}"}).encode()
        raise urllib.error.HTTPError(url, 404, "Not Found", hdrs=None, fp=None)


def picked(fake: Fake) -> list[tuple[str, str]]:
    return [(r.name, r.tag) for r in releases.choose(fake, "me")]


class Choose(unittest.TestCase):
    def test_the_two_newest_releases_win(self):
        fake = Fake([repo("a"), repo("b"), repo("c")],
                    {"a": release("a", "v1.0.0", "2026-09-20"), "b": release("b", "v1.9.1", "2026-09-26"),
                     "c": release("c", "v2.0.0", "2026-09-25")})
        self.assertEqual(picked(fake), [("b", "v1.9.1"), ("c", "v2.0.0")])

    def test_forks_archived_and_unreleased_repositories_are_left_out(self):
        fake = Fake([repo("fork", fork=True), repo("old", archived=True), repo("none"), repo("kept")],
                    {"fork": release("fork", "v9.0.0", "2026-09-27"), "old": release("old", "v9.0.0", "2026-09-27"),
                     "kept": release("kept", "v1.2.3", "2026-09-01")})
        self.assertEqual(picked(fake), [("kept", "v1.2.3")])

    def test_drafts_and_prereleases_do_not_count(self):
        fake = Fake([repo("a"), repo("b")], {"a": release("a", "v2.0.0-rc1", "2026-09-27", prerelease=True),
                                              "b": release("b", "v1.0.0", "2026-09-02")})
        self.assertEqual(picked(fake), [("b", "v1.0.0")])


class Placard(unittest.TestCase):
    def test_a_placard_shows_the_version_the_day_and_the_pin(self):
        fake = Fake([repo("kit")], {"kit": release("kit", "v1.9.1", "2026-09-26")}, majors={"kit@v1"})
        card = releases.placard(releases.choose(fake, "me")[0])
        self.assertEqual({k: card[k] for k in ("kind", "owner", "name", "icon", "link")},
                         {"kind": "placard", "owner": "me", "name": "kit", "icon": "package",
                          "link": "https://github.com/me/kit/releases/tag/v1.9.1"})
        self.assertEqual(card["desc"], "The kit kit, drawn as committed SVGs.")
        self.assertEqual(card["cells"], [["Release", "V1.9.1"], ["Published", "26 SEP"], ["Pinned as", "@V1"]])

    def test_the_day_a_release_shipped_is_its_day_in_est(self):
        # 02:00 UTC on the 26th is 21:00 EST on the 25th.
        late = release("kit", "v1.9.1", "2026-09-26", published_at="2026-09-26T02:00:00Z")
        card = releases.placard(releases.choose(Fake([repo("kit")], {"kit": late}), "me")[0])
        self.assertEqual(card["cells"][1], ["Published", "25 SEP"])

    def test_without_a_major_tag_the_language_shows_instead(self):
        card = releases.placard(releases.choose(Fake([repo("kit")], {"kit": release("kit", "v1.9.1", "2026-09-26")}), "me")[0])
        self.assertEqual(card["cells"][2], ["Language", "PYTHON"])

    def test_a_long_description_is_cut_at_its_first_sentence(self):
        long = "Documented standards and the workflows that enforce them. " + "More words follow here. " * 10
        self.assertEqual(releases.about(long), "Documented standards and the workflows that enforce them.")

    def test_one_long_sentence_is_cut_at_its_first_clause(self):
        long = ("Blueprint headers, footers and body elements a README draws for itself: measured from GitHub and "
                "git on a schedule, drawn as committed SVGs, never fetched.")
        self.assertEqual(releases.about(long), "Blueprint headers, footers and body elements a README draws for itself.")
        self.assertTrue(releases.about("Note: " + "word " * 40).startswith("Note: word"))


SETTINGS = """banners:
  motto: Built to be rebuilt.
elements:
  how-it-fits:
    kind: schematic
  # releases:start  written by releases.py
  # releases:end
trophies:
  style: trophy
"""


class Data(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / ".github" / "markdown.yaml"
        self.settings.parent.mkdir()
        self.settings.write_text(SETTINGS, encoding="utf-8")
        self.fake = Fake([repo("a"), repo("b")], {"a": release("a", "v1.0.0", "2026-09-20"),
                                                   "b": release("b", "v1.1.0", "2026-09-26")})

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, fake: Fake) -> str:
        releases.main([str(self.settings), "--owner", "me"], fetch=fake)
        return self.settings.read_text(encoding="utf-8")

    def test_the_settings_name_both_slots_and_leave_the_print_to_the_stub(self):
        self.run_main(self.fake)
        doc = releases.read(self.settings, releases.REGION)
        self.assertEqual(list(doc["elements"]), ["release-1", "release-2"])
        for card in doc["elements"].values():
            self.assertNotIn("print", card, "the kit draws them in the stub's theme")

    def test_the_region_reads_back_as_it_was_written(self):
        self.run_main(self.fake)
        wanted = releases.document(releases.choose(self.fake, "me", ""))
        self.assertEqual(releases.read(self.settings, releases.REGION), json.loads(json.dumps(wanted)))

    def test_only_the_region_is_rewritten(self):
        def outside(text: str) -> str:
            start = text.index("\n", text.index("  # releases:start")) + 1
            return text[:start] + text[text.index("  # releases:end"):]
        text = self.run_main(self.fake)
        self.assertIn("  release-1:\n    kind: \"placard\"\n", text)
        self.assertEqual(outside(text), outside(SETTINGS))

    def test_an_unreachable_github_keeps_last_weeks_placards(self):
        before = self.run_main(self.fake)
        self.assertEqual(self.run_main(Fake([], {}, fail=True)), before)

    def test_a_first_run_with_nothing_writes_nothing(self):
        self.assertEqual(self.run_main(Fake([], {}, fail=True)), SETTINGS)

    def test_settings_without_the_region_are_refused(self):
        self.settings.write_text("elements:\n  how-it-fits:\n    kind: schematic\n", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.run_main(self.fake)

    def test_no_banned_dash_reaches_the_file(self):
        text = self.run_main(Fake([repo("a", description="Kits " + DASHES[1] + " drawn " + DASHES[0] + " daily")],
                                  {"a": release("a", "v1.0.0", "2026-09-20")}))
        for ch in DASHES:
            self.assertNotIn(ch, text)


if __name__ == "__main__":
    unittest.main()
