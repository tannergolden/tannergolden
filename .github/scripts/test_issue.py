# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The good first issues, offline: GitHub's search answers come from fixtures.

  python3 -m unittest discover -s .github/scripts -p 'test_*.py'

The fixtures are shaped like the search API's responses, with made-up
projects, so nothing here touches the network.
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # issue.py imports placards.py beside it
spec = importlib.util.spec_from_file_location("issue", HERE / "issue.py")
issue = importlib.util.module_from_spec(spec)
sys.modules["issue"] = issue  # dataclasses look their module up while the class is built
spec.loader.exec_module(issue)
TODAY = dt.date(2026, 9, 28)
DASHES = [chr(cp) for cp in (0x2013, 0x2014, 0x2015)]


def repo(name: str, stars: int, **extra) -> dict:
    return {"full_name": name, "html_url": f"https://github.com/{name}", "stargazers_count": stars, "language": "Go",
            "description": f"The {name.split('/')[1]} project.", "archived": False, "fork": False, **extra}


def item(name: str, number: int, created: str, **extra) -> dict:
    return {"number": number, "title": f"Document the export flag ({number})",
            "html_url": f"https://github.com/{name}/issues/{number}", "repository_url": f"https://api.github.com/repos/{name}",
            "state": "open", "locked": False, "assignee": None, "assignees": [], "comments": 1,
            "created_at": f"{created}T09:00:00Z", "labels": [{"name": "good first issue"}], **extra}


REPOS = [repo("big/one", 90_000), repo("mid/two", 40_000), repo("small/three", 1_500),
         repo("gone/four", 80_000, archived=True), repo("fork/five", 70_000, fork=True)]


class Fake:
    """Answers the search API from a table: the projects, then issues by the projects a query names."""

    def __init__(self, issues: list[dict], repos: list[dict] = REPOS, fail: bool = False):
        self.issues, self.repos, self.fail, self.urls = issues, repos, fail, []

    def __call__(self, url: str, headers: dict) -> bytes:
        self.urls.append(url)
        if self.fail:
            raise urllib.error.URLError("unreachable")
        if "/search/repositories" in url:
            return json.dumps({"items": self.repos}).encode()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)["q"][0]
        since = dt.date.fromisoformat(q.split("created:>=")[1].split()[0])
        names = {part[5:].lower() for part in q.split() if part.startswith("repo:")}
        hits = [it for it in self.issues if issue.repo_of(it) in names and dt.date.fromisoformat(it["created_at"][:10]) >= since]
        return json.dumps({"items": hits}).encode()


def picked(fake: Fake, **kw) -> list[tuple[str, int]]:
    return [(f"{p.owner}/{p.name}", p.number) for p in issue.choose(fake, TODAY, pause=0, **kw)]


class Draw(unittest.TestCase):
    def test_the_two_most_starred_projects_give_their_newest_issue(self):
        fake = Fake([item("mid/two", 1, "2026-09-22"), item("mid/two", 2, "2026-09-25"), item("small/three", 3, "2026-09-26")])
        self.assertEqual(picked(fake), [("mid/two", 2), ("small/three", 3)])

    def test_taken_or_unfit_issues_are_skipped(self):
        unfit = [item("big/one", 1, "2026-09-26", assignee={"login": "someone"}),
                 item("big/one", 2, "2026-09-26", pull_request={"url": "https://api.github.com/x"}),
                 item("big/one", 3, "2026-09-26", locked=True),
                 item("big/one", 4, "2026-09-26", state="closed"),
                 item("big/one", 5, "2026-09-26", title="Win a prize at https://example.com")]
        fake = Fake(unfit + [item("mid/two", 6, "2026-09-23"), item("small/three", 7, "2026-09-24")])
        self.assertEqual(picked(fake), [("mid/two", 6), ("small/three", 7)])

    def test_archived_forked_and_small_projects_are_left_out(self):
        fake = Fake([item("gone/four", 1, "2026-09-26"), item("fork/five", 2, "2026-09-26"),
                     item("tiny/six", 3, "2026-09-26"), item("small/three", 4, "2026-09-24")],
                    repos=REPOS + [repo("tiny/six", 500)])
        self.assertEqual(picked(fake), [("small/three", 4)])

    def test_a_quiet_week_looks_back_a_month(self):
        self.assertEqual(picked(Fake([item("big/one", 1, "2026-09-10"), item("mid/two", 2, "2026-09-26")])),
                         [("big/one", 1), ("mid/two", 2)])

    def test_one_project_never_fills_both_slots(self):
        self.assertEqual(picked(Fake([item("big/one", n, f"2026-09-2{n}") for n in (1, 2, 3)])), [("big/one", 3)])

    def test_nothing_recent_picks_nothing(self):
        self.assertEqual(picked(Fake([item("big/one", 1, "2026-06-01")])), [])

    def test_a_title_the_kit_cannot_letter_is_passed_over(self):
        cjk = "".join(chr(c) for c in range(0x4E00, 0x4E14))
        fake = Fake([item("big/one", 1, "2026-09-26", title=cjk), item("big/one", 2, "2026-09-24")])
        self.assertEqual(picked(fake), [("big/one", 2)])

    def test_the_query_asks_for_open_unassigned_unlinked_issues(self):
        fake = Fake([item("big/one", 1, "2026-09-26")])
        issue.choose(fake, TODAY, pause=0)
        self.assertIn("/search/repositories", fake.urls[0])
        q = urllib.parse.parse_qs(urllib.parse.urlparse(fake.urls[1]).query)["q"][0]
        for part in ('label:"good first issue"', "is:issue", "is:open", "no:assignee", "-linked:pr",
                     "archived:false", "created:>=2026-09-21", "repo:big/one"):
            self.assertIn(part, q)
        self.assertNotIn("repo:gone/four", q)
        self.assertNotIn("repo:fork/five", q)

    def test_the_search_stops_once_both_slots_are_filled(self):
        fake = Fake([item("mid/two", 1, "2026-09-26"), item("small/three", 2, "2026-09-26")])
        self.assertEqual(picked(fake, batch=1), [("mid/two", 1), ("small/three", 2)])
        self.assertEqual(len(fake.urls), 4)  # the projects, then big/one, mid/two and small/three, one each


class Text(unittest.TestCase):
    def test_titles_from_strangers_become_plain_letterable_text(self):
        raw = "<b>Fix</b> the " + DASHES[1] + " parser " + chr(0x1F680) + " for &amp; tokens " + "and more " * 30
        out = issue.letterable(raw)
        self.assertTrue(out.startswith("Fix the - parser for & tokens and more"), out)
        self.assertTrue(out.endswith(chr(0x2026)))
        self.assertLessEqual(len(out), 150)
        self.assertTrue(all(ch in issue.LETTERS for ch in out))

    def test_a_title_mostly_in_another_script_is_refused(self):
        self.assertIsNone(issue.letterable("Fix " + "".join(chr(c) for c in range(0x4E00, 0x4E10))))
        self.assertEqual(issue.letterable("Résumé parsing for café menus"), "Résumé parsing for café menus")

    def test_stars_are_counted_the_way_github_shows_them(self):
        for n, s in ((999, "999"), (1_000, "1K"), (1_500, "1.5K"), (48_213, "48.2K"), (181_234, "181K"), (1_234_567, "1.2M")):
            self.assertEqual(issue.compact(n), s)


class Placards(unittest.TestCase):
    def pick(self) -> "issue.Pick":
        return issue.choose(Fake([item("big/one", 7, "2026-09-26")]), TODAY, pause=0)[0]

    def test_a_placard_carries_the_project_and_the_issue(self):
        card = issue.placard(self.pick())
        self.assertEqual({k: card[k] for k in ("kind", "owner", "name", "icon", "link")},
                         {"kind": "placard", "owner": "big", "name": "one", "icon": "flag",
                          "link": "https://github.com/big/one/issues/7"})
        self.assertEqual(card["desc"], "#7: Document the export flag (7).")
        self.assertEqual(card["cells"], [["Stars", "90K"], ["Language", "GO"], ["Opened", "26 SEP"]])

    def test_the_day_an_issue_opened_is_its_day_in_est(self):
        # 02:00 UTC on the 26th is 21:00 EST on the 25th.
        late = item("big/one", 7, "2026-09-26", created_at="2026-09-26T02:00:00Z")
        pick = issue.choose(Fake([late]), TODAY, pause=0)[0]
        self.assertEqual(pick.opened, dt.date(2026, 9, 25))
        self.assertEqual(issue.placard(pick)["cells"][2], ["Opened", "25 SEP"])

    def test_an_empty_slot_opens_githubs_own_search(self):
        doc = issue.document([self.pick()])
        self.assertEqual(list(doc["elements"]), ["issue-1", "issue-2"])
        self.assertEqual(doc["elements"]["issue-2"]["link"], issue.BROWSE)
        self.assertEqual(list(issue.document([])["elements"]), ["issue-1"])

    def test_every_placard_has_what_the_kit_needs(self):
        for card in issue.document([self.pick()])["elements"].values():
            for key in ("owner", "name", "desc", "cells"):
                self.assertTrue(card[key], key)
            self.assertEqual(len(card["cells"]), 3)


class Data(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name) / ".github" / "good-first-issue.json"

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, fake: Fake) -> str:
        issue.main([str(self.data), "--today", TODAY.isoformat()], fetch=fake, pause=0)
        return self.data.read_text(encoding="utf-8")

    def test_the_data_file_is_the_kits_json(self):
        doc = json.loads(self.run_main(Fake([item("big/one", 1, "2026-09-26"), item("mid/two", 2, "2026-09-25")])))
        self.assertEqual([c["link"] for c in doc["elements"].values()],
                         ["https://github.com/big/one/issues/1", "https://github.com/mid/two/issues/2"])

    def test_an_unreachable_github_keeps_last_weeks_placards(self):
        first = self.run_main(Fake([item("big/one", 1, "2026-09-26")]))
        self.assertEqual(self.run_main(Fake([], fail=True)), first)

    def test_a_first_run_with_nothing_writes_the_search_placard(self):
        doc = json.loads(self.run_main(Fake([], fail=True)))
        self.assertEqual([c["link"] for c in doc["elements"].values()], [issue.BROWSE])

    def test_no_banned_dash_reaches_the_file(self):
        text = self.run_main(Fake([item("big/one", 1, "2026-09-26", title="Fix " + DASHES[0] + " and " + DASHES[1] + " in docs")]))
        for ch in DASHES:
            self.assertNotIn(ch, text)


if __name__ == "__main__":
    unittest.main()
