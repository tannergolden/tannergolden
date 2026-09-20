# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every source adapter, against a recorded shape of what its API returns.

The fixtures are the documented formats: a GitHub release object, the
advisories list, endoflife.date's two cycle shapes, the RFC Editor's per-RFC
JSON, and a Lobsters story. A change to any adapter is caught here before a
random moment finds it on the page.

Every kind reports news, so every fixture carries a timestamp relative to
`NOW` rather than a fixed date: a test that passes today and fails in three
weeks is a test of the calendar.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import phrasing
import sources
from state import Ledger

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()
HOUSE = re.compile(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\): (?P<subject>.+)$")


def ago(days: float) -> str:
    """An ISO timestamp that many days in the past, as every one of these APIs writes it."""
    return (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def ledger(repo):
    return Ledger("state/ledger.json")


def assert_well_formed(entry):
    from render import commit_message
    from text import is_clean

    message = commit_message(entry)
    header = message.split("\n", 1)[0]
    assert HOUSE.match(header) and len(header) <= 72, header
    assert is_clean(message)
    assert entry.source_url.startswith("https://")
    assert entry.license and entry.body


def only(repo_name: str, product: str, monkeypatch):
    """Narrow the watchlist to one repository, so a fixture can answer for it."""
    monkeypatch.setattr(sources, "WATCHLIST", ((repo_name, product),))


# --- feat(release) --------------------------------------------------------------

def release(**overrides) -> dict:
    payload = {
        "tag_name": "v1.25.0",
        "draft": False,
        "prerelease": False,
        "published_at": ago(2),
        "html_url": "https://github.com/golang/go/releases/tag/v1.25.0",
        "body": "## Changes\n\nThe garbage collector now returns memory to the operating "
                "system more eagerly on Linux.\n\n* a bullet nobody needs\n",
    }
    payload.update(overrides)
    return payload


def test_release_reports_the_version_and_the_first_paragraph(repo, fake_net, seeded, monkeypatch):
    only("golang/go", "Go", monkeypatch)
    fake_net.json("https://api.github.com/repos/golang/go/releases/latest", release())

    entry = sources.fetch_release(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.kind == "release" and entry.commit_type == "feat"
    assert entry.identifier == "golang/go@v1.25.0"

    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["release"]
    # The leading v is a tag convention, not part of the version.
    assert rest == "Go 1.25.0" and entry.title == "Go 1.25.0"
    assert "Go 1.25.0" in entry.body or "1.25.0" in entry.body
    assert "garbage collector" in entry.body
    assert "## Changes" not in entry.body and "* a bullet" not in entry.body


def test_release_skips_drafts_prereleases_and_anything_stale(repo, fake_net, seeded, monkeypatch):
    only("golang/go", "Go", monkeypatch)
    for bad in ({"draft": True}, {"prerelease": True}, {"published_at": ago(400)}, {"tag_name": ""}):
        fake_net.jsons.clear()
        fake_net.json("https://api.github.com/repos/golang/go/releases/latest", release(**bad))
        assert sources.fetch_release(ledger(repo), TODAY) is None, bad


def test_release_never_repeats_a_tag(repo, fake_net, seeded, monkeypatch):
    only("golang/go", "Go", monkeypatch)
    fake_net.json("https://api.github.com/repos/golang/go/releases/latest", release())
    led = ledger(repo)
    led.remember("release", "golang/go@v1.25.0")
    assert sources.fetch_release(led, TODAY) is None


def test_release_keeps_a_tag_that_is_not_a_version_verbatim(repo, fake_net, seeded, monkeypatch):
    only("sqlite/sqlite", "SQLite", monkeypatch)
    fake_net.json("https://api.github.com/repos/sqlite/sqlite/releases/latest",
                  release(tag_name="version-3.50.0", html_url="https://github.com/sqlite/sqlite/releases"))
    entry = sources.fetch_release(ledger(repo), TODAY)
    assert entry is not None and entry.title == "SQLite version-3.50.0"


def test_release_survives_a_repository_that_stopped_publishing(repo, fake_net, seeded, monkeypatch):
    only("nginx/nginx", "nginx", monkeypatch)  # nothing registered: a 404 answers None
    assert sources.fetch_release(ledger(repo), TODAY) is None


# --- security(advisory) ----------------------------------------------------------

def advisory(**overrides) -> dict:
    payload = {
        "ghsa_id": "GHSA-abcd-1234-efgh",
        "cve_id": "CVE-2026-1111",
        "summary": "Prototype pollution in the merge helper",
        "published_at": ago(1),
        "html_url": "https://github.com/advisories/GHSA-abcd-1234-efgh",
        "vulnerabilities": [
            {"package": {"name": "left-pad", "ecosystem": "npm"}, "vulnerable_version_range": "< 4.2.1"}
        ],
    }
    payload.update(overrides)
    return payload


def test_advisory_names_the_package_the_range_and_the_cve(repo, fake_net, seeded):
    fake_net.json("https://api.github.com/advisories", [advisory()])
    entry = sources.fetch_advisory(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.commit_type == "security" and entry.identifier == "GHSA-abcd-1234-efgh"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["advisory"]
    assert "left-pad" in entry.subject and "left-pad" in entry.title
    for fact in ("left-pad", "npm", "< 4.2.1", "CVE-2026-1111", "Prototype pollution"):
        assert fact in entry.body, fact


def test_a_go_module_path_does_not_eat_the_whole_subject(repo, fake_net, seeded):
    """The case a real run produced, and the subject it truncated to nothing.

    `security(advisory): ...surface the critical advisory in
    github.com/kcp-dev/kcp` is 78 characters, so the ceiling cut it at
    "in" and the git log line named no package at all. The host goes.
    """
    fake_net.json("https://api.github.com/advisories", [advisory(
        vulnerabilities=[{"package": {"name": "github.com/kcp-dev/kcp", "ecosystem": "go"},
                          "vulnerable_version_range": "< 0.31.4"}])])
    entry = sources.fetch_advisory(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)

    from render import commit_message
    header = commit_message(entry).split("\n", 1)[0]
    assert "kcp-dev/kcp" in header, header
    assert not header.endswith("\u2026"), header
    # The page has no ceiling, so it keeps the name the advisory gave.
    assert "github.com/kcp-dev/kcp" in entry.title
    assert "github.com/kcp-dev/kcp" in entry.body


def test_a_package_name_keeps_every_segment_that_is_not_a_host(repo, fake_net, seeded):
    assert sources._package_label("@babel/core") == "@babel/core"
    assert sources._package_label("left-pad") == "left-pad"
    assert sources._package_label("org.apache.commons:commons-text") == "org.apache.commons:commons-text"
    assert sources._package_label("github.com/kcp-dev/kcp") == "kcp-dev/kcp"


def test_advisory_survives_an_entry_with_no_affected_package(repo, fake_net, seeded):
    fake_net.json("https://api.github.com/advisories", [advisory(vulnerabilities=[], cve_id="", summary="")])
    entry = sources.fetch_advisory(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert "GHSA-abcd-1234-efgh" in entry.subject


def test_advisory_skips_the_stale_and_the_seen(repo, fake_net, seeded):
    fake_net.json("https://api.github.com/advisories", [advisory(published_at=ago(90))])
    assert sources.fetch_advisory(ledger(repo), TODAY) is None

    fake_net.jsons.clear()
    fake_net.json("https://api.github.com/advisories", [advisory()])
    led = ledger(repo)
    led.remember("advisory", "GHSA-abcd-1234-efgh")
    assert sources.fetch_advisory(led, TODAY) is None


# --- chore(eol) -------------------------------------------------------------------

def test_eol_reads_the_long_lived_array_shape(repo, fake_net, seeded):
    soon = (TODAY + timedelta(days=30)).isoformat()
    fake_net.json(sources.EOL_ALL, ["python"])
    fake_net.json("https://endoflife.date/api/python.json",
                  [{"cycle": "3.9", "eol": soon, "latest": "3.9.23"},
                   {"cycle": "3.13", "eol": False, "latest": "3.13.2"}])

    entry = sources.fetch_eol(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.commit_type == "chore" and entry.identifier == "python-3.9"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["eol"]
    assert "Python 3.9" in entry.body and "30 days" in entry.body
    assert "3.9.23" in entry.body
    assert entry.source_url == "https://endoflife.date/python"


def test_eol_reads_the_wrapped_shape_too(repo, fake_net, seeded):
    fake_net.json(sources.EOL_ALL, ["ubuntu"])
    fake_net.json("https://endoflife.date/api/ubuntu.json",
                  {"result": {"releases": [{"name": "20.04", "eol": TODAY.isoformat(), "latest": "20.04.6"}]}})
    entry = sources.fetch_eol(ledger(repo), TODAY)
    assert entry is not None and entry.identifier == "ubuntu-20.04"
    assert "end of life today" in entry.body


def test_eol_reports_what_just_expired_and_ignores_the_far_future(repo, fake_net, seeded):
    fake_net.json(sources.EOL_ALL, ["nodejs"])
    fake_net.json("https://endoflife.date/api/nodejs.json",
                  [{"cycle": "18", "eol": (TODAY - timedelta(days=3)).isoformat()}])
    entry = sources.fetch_eol(ledger(repo), TODAY)
    assert entry is not None and "3 days ago" in entry.body

    fake_net.jsons.clear()
    fake_net.json(sources.EOL_ALL, ["nodejs"])
    fake_net.json("https://endoflife.date/api/nodejs.json",
                  [{"cycle": "24", "eol": (TODAY + timedelta(days=900)).isoformat()}])
    assert sources.fetch_eol(ledger(repo), TODAY) is None


def test_eol_survives_a_malformed_date(repo, fake_net, seeded):
    fake_net.json(sources.EOL_ALL, ["mystery"])
    fake_net.json("https://endoflife.date/api/mystery.json", [{"cycle": "1", "eol": "whenever"}])
    assert sources.fetch_eol(ledger(repo), TODAY) is None


# --- docs(rfc) ---------------------------------------------------------------------

def rfc_json(n: int, **overrides) -> dict:
    payload = {
        "doc_id": f"RFC{n}",
        "title": f"Title Of {n} - With A Dash",
        "pub_date": f"{TODAY.year} September",
        "status": "PROPOSED STANDARD",
        "abstract": "<p>The first paragraph.</p><p>The second one.</p>",
        "authors": ["A. Author", "B. Other"],
    }
    payload.update(overrides)
    return payload


def test_rfc_reads_the_editor_record(repo, fake_net, seeded):
    fake_net.json("https://www.rfc-editor.org/rfc/rfc", lambda url: rfc_json(int(re.search(r"rfc(\d+)\.json", url).group(1))))
    entry = sources.fetch_rfc(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    n = int(entry.identifier)
    assert sources.RFC_CEILING - sources.RFC_RECENT <= n <= sources.RFC_CEILING

    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["rfc"]
    assert rest.startswith(f"RFC {n}, Title Of {n} - With A Dash")
    assert not entry.body.startswith(f"RFC {n}")
    assert "proposed standard" in entry.body
    # The abstract arrives as HTML paragraphs and reaches the body as prose.
    assert "The first paragraph." in entry.body and "<p>" not in entry.body
    assert entry.attribution == "A. Author, B. Other"


def test_rfc_refuses_anything_that_is_not_recent(repo, fake_net, seeded):
    fake_net.json("https://www.rfc-editor.org/rfc/rfc", rfc_json(9000, pub_date="1998 April"))
    assert sources.fetch_rfc(ledger(repo), TODAY) is None


def test_rfc_walks_the_ceiling_down_past_the_end_of_the_series(repo, fake_net, seeded):
    # Nothing registered: every number answers None, which is what a number
    # past the end of the series answers.
    assert sources.fetch_rfc(ledger(repo), TODAY) is None


def test_rfc_skips_unissued_numbers(repo, fake_net, seeded):
    fake_net.json("https://www.rfc-editor.org/rfc/rfc", rfc_json(9000, title="Not Issued"))
    assert sources.fetch_rfc(ledger(repo), TODAY) is None


# --- docs(lobsters) -----------------------------------------------------------------

def story(**overrides) -> dict:
    payload = {
        "short_id": "abc123",
        "title": "A thing somebody learned the hard way",
        "url": "https://example.invalid/post",
        "score": 42,
        "comments_url": "https://lobste.rs/s/abc123/a-thing",
        "tags": ["programming", "practices"],
        "created_at": ago(1),
        "submitter_user": {"username": "someone"},
    }
    payload.update(overrides)
    return payload


def test_lobsters_reports_the_score_the_domain_and_the_tags(repo, fake_net, seeded):
    fake_net.json(sources.LOBSTERS, [story()])
    entry = sources.fetch_lobsters(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.commit_type == "docs" and entry.identifier == "abc123"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["lobsters"]
    assert "42 points" in entry.body
    assert "example.invalid" in entry.body
    assert "programming, practices" in entry.body
    assert entry.attribution == "submitted by someone"
    assert entry.extra_links == [("discussion", "https://lobste.rs/s/abc123/a-thing")]


def test_lobsters_will_not_offer_a_demonstrably_old_story(repo, fake_net, seeded):
    """The hottest list is current by construction. This is the guard for when it is not."""
    fake_net.json(sources.LOBSTERS, [story(created_at=ago(120))])
    assert sources.fetch_lobsters(ledger(repo), TODAY) is None

    fake_net.jsons.clear()
    fake_net.json(sources.LOBSTERS, [story(created_at=ago(2))])
    assert sources.fetch_lobsters(ledger(repo), TODAY) is not None


def test_lobsters_still_offers_a_story_whose_date_it_cannot_read(repo, fake_net, seeded):
    """A guard, not the mechanism: an unparseable date must not take the kind dark."""
    for bad in ("", "not a date", None):
        fake_net.jsons.clear()
        fake_net.json(sources.LOBSTERS, [story(created_at=bad)])
        assert sources.fetch_lobsters(ledger(repo), TODAY) is not None, bad


def test_lobsters_ignores_anything_under_the_score_floor(repo, fake_net, seeded):
    fake_net.json(sources.LOBSTERS, [story(score=sources.LOBSTERS_FLOOR - 1)])
    assert sources.fetch_lobsters(ledger(repo), TODAY) is None


def test_lobsters_falls_back_to_the_thread_for_a_text_post(repo, fake_net, seeded):
    fake_net.json(sources.LOBSTERS, [story(url="")])
    entry = sources.fetch_lobsters(ledger(repo), TODAY)
    assert entry is not None and entry.source_url == "https://lobste.rs/s/abc123/a-thing"
    assert "lobste.rs" in entry.body


def test_lobsters_refuses_a_link_that_is_not_https(repo, fake_net, seeded):
    fake_net.json(sources.LOBSTERS, [story(url="javascript:alert(1)", comments_url="")])
    assert sources.fetch_lobsters(ledger(repo), TODAY) is None


# --- the picker ------------------------------------------------------------------------

def test_picker_falls_through_a_failing_source_to_the_next(repo, fake_net, seeded, monkeypatch):
    calls = []

    def boom(ledger, today):
        calls.append("boom")
        raise RuntimeError("source down")

    def empty(ledger, today):
        calls.append("empty")
        return None

    def works(ledger, today):
        calls.append("works")
        return sources.Dispatch(kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 1, Host Software", title="RFC 1", body="b", identifier="1", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc1", license="freely reproducible")

    monkeypatch.setattr(sources, "FETCHERS", {"a": boom, "b": empty, "c": works})
    # A fixed order, so this is a test of the fall-through and not of the dice.
    monkeypatch.setattr(sources, "draw_order", lambda: ["a", "b", "c"])
    entry = sources.pick_dispatch(ledger(repo), TODAY)
    assert entry is not None and entry.identifier == "1"
    assert calls == ["boom", "empty", "works"]


def test_draw_order_offers_every_kind_exactly_once():
    for _ in range(20):
        order = sources.draw_order()
        assert sorted(order) == sorted(sources.KINDS)


def test_every_kind_has_a_fetcher_and_a_verb_pool():
    assert set(sources.FETCHERS) == set(sources.KINDS)
    for kind in sources.KINDS:
        assert phrasing.VERBS[kind], kind


def test_a_quiet_day_writes_nothing(repo, fake_net, seeded):
    """Nothing registered, so every source answers None. News, or silence."""
    assert sources.pick_dispatch(ledger(repo), TODAY) is None
