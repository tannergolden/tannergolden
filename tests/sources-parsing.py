# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every source adapter, against a recorded shape of what its API returns.

The fixtures are the documented formats: the Hacker News item shape, the
repository search payload, and a Lobsters story. A change to any adapter is
caught here before a random moment finds it on the page.

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


# --- the shared link claim ----------------------------------------------------

def test_one_url_has_one_spelling(repo):
    """Two sources point at one article with different punctuation and tracking."""
    same = sources._canonical
    assert same("https://www.example.com/post/?utm_source=hn") == same("https://example.com/post")
    assert same("https://x.example/a/") == same("https://x.example/a")
    assert same("https://x.example/a?b=1&c=2") == same("https://x.example/a?c=2&b=1")
    assert same("https://x.example/a") != same("https://x.example/b")
    # Anything that is not a fetchable page claims nothing.
    assert same("javascript:alert(1)") == "" and same("") == "" and same("not a url") == ""


def test_a_story_on_two_sources_is_sent_once(repo, fake_net, seeded):
    """The same link reaches Hacker News and Lobsters on the same morning."""
    shared = "https://blog.example/why-we-rewrote-it"
    fake_net.json(sources.HN_TOP, [101])
    fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json",
                  hn_item(url=shared + "/?utm_source=hn"))
    fake_net.json(sources.LOBSTERS, [story(url=shared)])

    led = ledger(repo)
    first = sources.fetch_hn(led, TODAY)
    assert first is not None and first.kind == "hn"
    # Nothing is claimed yet: a candidate is not a dispatch, and Lobsters
    # would still be free to offer it if this one never reached the page.
    assert sources.fetch_lobsters(led, TODAY) is not None

    # The sender claims it, which is what dispatches.py does once the entry
    # is on the page. Now the other aggregator has nothing new to say.
    sources.claim_link(led, first.source_url)
    assert sources.fetch_lobsters(led, TODAY) is None


def test_a_candidate_that_never_ships_does_not_burn_the_link(repo, fake_net, seeded):
    """A fetcher returning an entry the run then discards must cost nothing."""
    fake_net.json(sources.HN_TOP, [101])
    fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json", hn_item())
    led = ledger(repo)
    assert sources.fetch_hn(led, TODAY) is not None
    assert sources.fetch_hn(led, TODAY) is not None  # offered again, not spent


# --- docs(hn) -----------------------------------------------------------------

def hn_item(**overrides) -> dict:
    payload = {
        "type": "story",
        "title": "Why we rewrote it in Rust",
        "url": "https://blog.example/why-we-rewrote-it",
        "score": 412,
        "descendants": 188,
        "time": int((NOW - timedelta(hours=6)).timestamp()),
    }
    payload.update(overrides)
    return payload


def test_hn_reports_the_score_the_domain_and_the_conversation(repo, fake_net, seeded):
    fake_net.json(sources.HN_TOP, [101])
    fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json", hn_item())
    entry = sources.fetch_hn(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.kind == "hn" and entry.commit_type == "docs" and entry.identifier == "101"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["hn"]
    assert entry.title == "Why we rewrote it in Rust"
    assert "412 points" in entry.body and "blog.example" in entry.body
    assert "188 comments" in entry.body
    assert entry.extra_links == [("discussion", "https://news.ycombinator.com/item?id=101")]


def test_hn_ignores_anything_that_is_not_on_the_front_page(repo, fake_net, seeded):
    """Below the floor is a story on its way up or on its way out."""
    fake_net.json(sources.HN_TOP, [101])
    fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json",
                  hn_item(score=sources.HN_FLOOR - 1))
    assert sources.fetch_hn(ledger(repo), TODAY) is None


def test_hn_skips_a_job_post_a_dead_story_and_a_poll(repo, fake_net, seeded):
    for bad in ({"type": "job"}, {"dead": True}, {"deleted": True}, {"title": ""}):
        fake_net.jsons.clear()
        fake_net.json(sources.HN_TOP, [101])
        fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json", hn_item(**bad))
        assert sources.fetch_hn(ledger(repo), TODAY) is None, bad


def test_hn_points_a_text_post_at_its_thread(repo, fake_net, seeded):
    fake_net.json(sources.HN_TOP, [101])
    fake_net.json("https://hacker-news.firebaseio.com/v0/item/101.json", hn_item(url=""))
    entry = sources.fetch_hn(ledger(repo), TODAY)
    assert entry is not None
    assert entry.source_url == "https://news.ycombinator.com/item?id=101"
    assert entry.extra_links == []  # no second link to the place it already points


# --- feat(trending) -----------------------------------------------------------

def trending_repo(**overrides) -> dict:
    payload = {
        "full_name": "someone/fast-thing",
        "html_url": "https://github.com/someone/fast-thing",
        "stargazers_count": 4200,
        "language": "Rust",
        "description": "A fast thing that replaces a slow thing",
        "created_at": ago(9),
    }
    payload.update(overrides)
    return payload


def test_trending_reports_the_stars_the_age_and_the_language(repo, fake_net, seeded):
    fake_net.json(sources.SEARCH, {"items": [trending_repo()]})
    entry = sources.fetch_trending(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)
    assert entry.kind == "trending" and entry.commit_type == "feat"
    assert entry.identifier == "someone/fast-thing" and entry.title == "someone/fast-thing"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["trending"]
    assert "4200 stars" in entry.body
    assert "9 days ago" in entry.body
    assert "A fast thing that replaces a slow thing." in entry.body
    assert "Written in Rust." in entry.body


def test_trending_asks_only_for_repositories_new_enough_to_be_trending(repo, fake_net, seeded):
    fake_net.json(sources.SEARCH, {"items": [trending_repo()]})
    sources.fetch_trending(ledger(repo), TODAY)
    asked = fake_net.requests[0]
    assert "created%3A%3E" in asked and f"stars%3A%3E%3D{sources.TRENDING_MIN_STARS}" in asked
    assert "sort=stars" in asked and "order=desc" in asked


def test_trending_survives_a_repository_with_no_description(repo, fake_net, seeded):
    fake_net.json(sources.SEARCH, {"items": [trending_repo(description="", language="")]})
    entry = sources.fetch_trending(ledger(repo), TODAY)
    assert entry is not None
    assert_well_formed(entry)


def test_trending_never_repeats_a_repository(repo, fake_net, seeded):
    fake_net.json(sources.SEARCH, {"items": [trending_repo()]})
    led = ledger(repo)
    led.remember("trending", "someone/fast-thing")
    assert sources.fetch_trending(led, TODAY) is None


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
