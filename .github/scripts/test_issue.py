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
import io
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
import placards  # noqa: E402  (beside issue.py, on the path set above)
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


def node(it: dict) -> dict:
    """A table issue the way GraphQL gives it: counts where REST gives lists."""
    taken = len(it.get("assignees") or []) + (1 if it.get("assignee") else 0)
    return {"number": it["number"], "title": it["title"], "url": it["html_url"], "createdAt": it["created_at"],
            "locked": it["locked"], "assignees": {"totalCount": taken},
            "closedByPullRequestsReferences": {"totalCount": it.get("linked", 0)}}


class Fake:
    """Answers from a table: the search API for the projects, GraphQL for each project's newest issues."""

    def __init__(self, issues: list[dict], repos: list[dict] = REPOS, fail: bool = False):
        self.issues, self.repos, self.fail, self.urls, self.queries = issues, repos, fail, [], []

    def __call__(self, url: str, headers: dict, data: bytes | None = None) -> bytes:
        self.urls.append(url)
        if self.fail:
            raise urllib.error.URLError("unreachable")
        if "/search/repositories" in url:
            return json.dumps({"items": self.repos}).encode()
        assert url.endswith("/graphql") and data is not None, url
        ask = json.loads(data)
        self.queries.append(ask)
        answer = {}
        for key, owner in ask["variables"].items():
            if key.startswith("o"):
                full = f"{owner}/{ask['variables']['n' + key[1:]]}".lower()
                # GitHub's answer: open issues only, never a pull request, newest first.
                mine = sorted((it for it in self.issues if issue.repo_of(it) == full and it["state"] == "open"
                               and "pull_request" not in it), key=lambda it: it["created_at"], reverse=True)
                answer["r" + key[1:]] = {"issues": {"nodes": [node(it) for it in mine[:issue.NEWEST]]}}
        return json.dumps({"data": answer}).encode()


def picked(fake: Fake, **kw) -> list[tuple[str, int]]:
    return [(f"{p.owner}/{p.name}", p.number) for p in issue.choose(fake, TODAY, **kw)]


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

    def test_one_query_asks_every_kept_project_for_its_newest_open_good_first_issues(self):
        fake = Fake([item("big/one", 1, "2026-09-26")])
        issue.choose(fake, TODAY)
        self.assertIn("/search/repositories", fake.urls[0])
        self.assertEqual(len(fake.queries), 1)
        query, variables = fake.queries[0]["query"], fake.queries[0]["variables"]
        for part in ('labels: ["good first issue"]', "states: OPEN", "orderBy: {field: CREATED_AT, direction: DESC}",
                     f"first: {issue.NEWEST}", "assignees { totalCount }", "closedByPullRequestsReferences"):
            self.assertIn(part, query)
        self.assertEqual(sorted(v for k, v in variables.items() if k.startswith("n")), ["one", "three", "two"])

    def test_an_issue_with_a_pull_request_on_the_way_is_skipped(self):
        fake = Fake([item("big/one", 1, "2026-09-26", linked=1), item("big/one", 2, "2026-09-25"),
                     item("mid/two", 3, "2026-09-24")])
        self.assertEqual(picked(fake), [("big/one", 2), ("mid/two", 3)])

    def test_the_queries_stop_once_both_slots_are_filled(self):
        fake = Fake([item("mid/two", 1, "2026-09-26"), item("small/three", 2, "2026-09-26")])
        self.assertEqual(picked(fake, batch=1), [("mid/two", 1), ("small/three", 2)])
        self.assertEqual(len(fake.urls), 4)  # the projects, then big/one, mid/two and small/three, one query each

    def test_graphql_answering_only_errors_is_github_unavailable(self):
        def fetch(url: str, headers: dict, data: bytes | None = None) -> bytes:
            if "/search/repositories" in url:
                return json.dumps({"items": REPOS}).encode()
            return b'{"errors": [{"message": "Something went wrong"}]}'
        with self.assertRaisesRegex(ValueError, "Something went wrong"):
            issue.choose(fetch, TODAY)


class RateLimits(unittest.TestCase):
    """A search GitHub turns away for a rate limit waits as asked; any other refusal says GitHub's reason."""

    def refusing(self, times: int, headers: dict, body: bytes = b"{}"):
        calls, waits = [], []

        def fetch(url: str, _headers: dict) -> bytes:
            calls.append(url)
            if len(calls) <= times:
                raise urllib.error.HTTPError(url, 403, "Forbidden", headers, io.BytesIO(body))
            return b'{"items": []}'
        return fetch, calls, waits

    def test_a_rate_limited_search_waits_as_asked_and_tries_again(self):
        fetch, calls, waits = self.refusing(1, {"retry-after": "7"})
        self.assertEqual(placards.github(fetch, "/search/issues", "t", {"q": "x"}, sleep=waits.append), {"items": []})
        self.assertEqual((len(calls), waits), (2, [7.0]))

    def test_a_secondary_limit_that_names_no_time_waits_a_minute(self):
        fetch, calls, waits = self.refusing(1, {}, b'{"message": "You have exceeded a secondary rate limit."}')
        placards.github(fetch, "/search/issues", "t", {"q": "x"}, sleep=waits.append)
        self.assertEqual(waits, [60.0])

    def test_a_limit_that_does_not_lift_gives_up_with_githubs_reason(self):
        fetch, calls, waits = self.refusing(9, {"retry-after": "5"}, b'{"message": "API rate limit exceeded."}')
        with self.assertRaises(urllib.error.HTTPError) as err:
            placards.github(fetch, "/search/issues", "t", {"q": "x"}, sleep=waits.append)
        self.assertEqual((len(calls), waits), (placards.RETRIES + 1, [5.0] * placards.RETRIES))
        self.assertIn("API rate limit exceeded", str(err.exception))

    def test_a_refusal_that_is_not_a_rate_limit_is_not_retried(self):
        fetch, calls, waits = self.refusing(1, {}, b'{"message": "Resource not accessible by integration"}')
        with self.assertRaises(urllib.error.HTTPError) as err:
            placards.github(fetch, "/search/issues", "t", {"q": "x"}, sleep=waits.append)
        self.assertEqual((len(calls), waits), (1, []))
        self.assertIn("Resource not accessible by integration", str(err.exception))
        self.assertIsNone(placards.wait_for(urllib.error.HTTPError("u", 403, "x", {"retry-after": "600"}, None), ""))


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
        return issue.choose(Fake([item("big/one", 7, "2026-09-26")]), TODAY)[0]

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
        pick = issue.choose(Fake([late]), TODAY)[0]
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


SETTINGS = """elements:
  how-it-fits:
    kind: schematic
  # issues:start  written by issue.py
  # issues:end
"""


class Data(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Path(self.tmp.name) / ".github" / "markdown.yaml"
        self.settings.parent.mkdir()
        self.settings.write_text(SETTINGS, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def run_main(self, fake: Fake) -> str:
        issue.main([str(self.settings), "--today", TODAY.isoformat()], fetch=fake)
        return self.settings.read_text(encoding="utf-8")

    def placards(self) -> dict:
        return issue.read(self.settings, issue.REGION)["elements"]

    def test_the_settings_hold_both_placards(self):
        self.run_main(Fake([item("big/one", 1, "2026-09-26"), item("mid/two", 2, "2026-09-25")]))
        self.assertEqual([c["link"] for c in self.placards().values()],
                         ["https://github.com/big/one/issues/1", "https://github.com/mid/two/issues/2"])
        self.assertEqual(list(self.placards()), list(issue.SLOTS))

    def test_an_unreachable_github_keeps_last_weeks_placards(self):
        first = self.run_main(Fake([item("big/one", 1, "2026-09-26")]))
        self.assertEqual(self.run_main(Fake([], fail=True)), first)

    def test_a_first_run_with_nothing_writes_the_search_placard(self):
        self.run_main(Fake([], fail=True))
        self.assertEqual([c["link"] for c in self.placards().values()], [issue.BROWSE])

    def test_only_the_region_is_rewritten(self):
        text = self.run_main(Fake([item("big/one", 1, "2026-09-26")]))
        self.assertTrue(text.startswith("elements:\n  how-it-fits:\n    kind: schematic\n  # issues:start"))
        self.assertTrue(text.endswith("  # issues:end\n"))

    def test_no_banned_dash_reaches_the_file(self):
        text = self.run_main(Fake([item("big/one", 1, "2026-09-26", title="Fix " + DASHES[0] + " and " + DASHES[1] + " in docs")]))
        for ch in DASHES:
            self.assertNotIn(ch, text)


if __name__ == "__main__":
    unittest.main()
