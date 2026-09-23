# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every kind of dispatch, and the picker that chooses between them.

Each fetcher returns one `Dispatch` the ledger has never seen, or None when
its source is down or has nothing new. None is an ordinary answer: the picker
moves to the next kind, and a run in which every source comes back empty writes
nothing and leaves the schedule untouched, so the next run tries again.

Two families. The three in this file are AGGREGATORS: Hacker News, Lobsters
and a trending repository list report what developers are reading and
starring right now, which is a fact about attention rather than about the
world. The nineteen in `feeds.py` are PUBLISHERS: projects announcing their
own releases, a public registry, and technology desks with named editors. One
says what people are looking at; the other says what happened.

EVERY DISPATCH LINKS SOMEWHERE A READER CAN OPEN. No source here is behind a
subscription, and `feeds.free_to_read` holds that for the links this file does
not choose: an aggregator reports what was submitted, and what was submitted
is frequently a payment form with a headline on it.

They overlap heavily, which is the whole reason the ledger keys on a
canonical URL as well as a per-source id: the same Ars Technica piece reaches
Hacker News and Lobsters the same morning, and a claim already taken is a
story already sent.

Nothing here is hand-written. Every source keeps producing, which is what
lets the ledger promise that no item appears twice without the well ever
running dry.

Every string that leaves a fetcher has been through `text.clean()`.
"""

from __future__ import annotations

import os
import random
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import feeds
import net
import phrasing
from config import NEWS_WINDOW_DAYS
from state import Ledger
from text import clean

_RNG = random.SystemRandom()


@dataclass
class Dispatch:
    """One dispatch, ready to be rendered into a commit and a page row."""

    kind: str  # the ledger key and the scope: hn, trending, lobsters
    commit_type: str  # feat, security, chore, docs
    emoji: str  # one emoji from the house mapping for that type
    subject: str  # lowercase imperative, without the type(scope) prefix
    title: str  # the short form shown in the page's table
    body: str  # prose for the commit body and the archive
    identifier: str  # what the ledger records; unique at the source
    source_name: str
    source_url: str
    license: str  # an SPDX identifier, or a short description when none fits
    attribution: str = ""  # authors or contributors, when the source names them
    extra_links: list = field(default_factory=list)  # (label, url) pairs

    @property
    def scope(self) -> str:
        return self.kind


# --- helpers ----------------------------------------------------------------

def _shuffled(items: list) -> list:
    items = list(items)
    _RNG.shuffle(items)
    return items


GITHUB_API = "https://api.github.com"


def _moment(stamp: str) -> datetime | None:
    """An ISO timestamp as an aware datetime, or None when it will not parse.

    Separate from `_fresh` because the two answers a caller needs are not the
    same: a source that reports no readable date is not a source reporting an
    old one, and treating them alike takes a whole kind dark on a field rename.
    """
    try:
        when = datetime.fromisoformat(clean(stamp).replace("Z", "+00:00"))
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def _stale(stamp: str, days: int = NEWS_WINDOW_DAYS) -> bool:
    """True only when a date reads AND falls outside the window. Unreadable is not stale."""
    when = _moment(stamp)
    return when is not None and not timedelta(0) <= datetime.now(timezone.utc) - when <= timedelta(days=days)


def _fresh(stamp: str, days: int = NEWS_WINDOW_DAYS) -> bool:
    """True when an ISO timestamp reads and is inside the window that counts as news."""
    return _moment(stamp) is not None and not _stale(stamp, days)


def _age(stamp: str) -> str:
    """How long ago, in words. Callers reach this past a freshness check."""
    when = _moment(stamp)
    if when is None:
        return "recently"
    days = (datetime.now(timezone.utc) - when).days
    return "today" if days < 1 else ("yesterday" if days == 1 else f"{days} days ago")


# --- what counts as the same story ------------------------------------------------

# Hacker News, Lobsters and a trending repository list carry the same link on
# the same morning more often than not. The ledger keys on a per-source id, so
# without this the page would run the same article three times under three
# scopes. Every kind also claims the canonical URL, and a claim already taken
# is a story already sent.
LINKS = "link"

_TRACKING = re.compile(r"^(utm_|ref_?$|ref_source|source$|fbclid$|gclid$)", re.IGNORECASE)


def _canonical(url: str) -> str:
    """One spelling of a URL, so two sources pointing at one article collide."""
    try:
        parts = urllib.parse.urlsplit(clean(url, command=True))
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return ""
    host = parts.netloc.lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    kept = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query) if not _TRACKING.match(k)]
    query = urllib.parse.urlencode(sorted(kept))
    return f"{host}{path}" + (f"?{query}" if query else "")


def _unclaimed(ledger: Ledger, url: str) -> bool:
    """True when no kind has sent this link before."""
    key = _canonical(url)
    return bool(key) and not ledger.seen(LINKS, key)


def claim_link(ledger: Ledger, url: str) -> None:
    """Record that this link has been sent.

    Called once the dispatch is on the page, not when a fetcher finds it: a
    candidate that never reaches the page must not burn the link for every
    other source that carries it.
    """
    key = _canonical(url)
    if key:
        ledger.remember(LINKS, key)


def _domain(url: str) -> str:
    return urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")


# --- docs(hn): the front page of Hacker News ---------------------------------------

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{id}.json"
HN_THREAD = "https://news.ycombinator.com/item?id={id}"

# The front page proper. Anything under this is on its way up or on its way
# out, and neither is what a reader means by "what is everyone reading".
HN_FLOOR = 100

# How far down the ranking to look. The list is ordered, so this is the front
# page and a little of the second.
HN_DEPTH = 40


def fetch_hn(ledger: Ledger, today: date) -> Dispatch | None:
    ids = net.get_json(HN_TOP)
    if not isinstance(ids, list):
        return None
    for story_id in _shuffled([i for i in ids[:HN_DEPTH] if isinstance(i, int)]):
        if ledger.seen("hn", str(story_id)):
            continue
        item = net.get_json(HN_ITEM.format(id=story_id))
        if not isinstance(item, dict) or item.get("type") != "story" or not item.get("title"):
            continue
        score = int(item.get("score") or 0)
        if score < HN_FLOOR or item.get("dead") or item.get("deleted"):
            continue

        thread = HN_THREAD.format(id=story_id)
        url = str(item.get("url") or "")
        if not url.startswith("https://"):
            url = thread  # a text post lives on the thread
        if not _unclaimed(ledger, url):
            continue
        # The front page runs the WSJ and the FT most weeks. An aggregator
        # reports what was submitted, and what was submitted is frequently a
        # payment form with a headline on it.
        if not feeds.free_to_read(url, str(item.get("title") or "")):
            continue

        comments = int(item.get("descendants") or 0)
        title = clean(str(item["title"]))
        where = _domain(url)
        body = phrasing.one_of(
            f"{score} points on Hacker News, from {where}.",
            f"Front page of Hacker News at {score} points; the source is {where}.",
            f"From {where}, and Hacker News has it at {score} points.",
        )
        if comments:
            body += f" {comments} comments so far."
        if item.get("time"):
            body += f" Posted {_age(datetime.fromtimestamp(int(item['time']), timezone.utc).isoformat())}."

        return Dispatch(
            kind="hn",
            commit_type="docs",
            emoji=phrasing.emoji_for("docs"),
            subject=f"{phrasing.verb_for('hn')} {title}",
            title=title,
            body=body,
            identifier=str(story_id),
            source_name="Hacker News",
            source_url=url,
            license="Title, score and link, reported as fact",
            extra_links=[("discussion", thread)] if url != thread else [],
        )
    return None


# --- feat(trending): a repository the industry is starring this month ----------------

SEARCH = f"{GITHUB_API}/search/repositories"

# Trending is new plus adopted. A repository created inside one of these
# windows and already near the top by stars is one people are picking up now,
# rather than one that has been famous for a decade.
TRENDING_WINDOWS = (14, 30, 90)
TRENDING_MIN_STARS = 150


def fetch_trending(ledger: Ledger, today: date) -> Dispatch | None:
    headers = net.github_headers(os.environ.get("GITHUB_TOKEN"))
    since = today - timedelta(days=_RNG.choice(TRENDING_WINDOWS))
    payload = net.get_json_with_headers(
        SEARCH,
        {"q": f"created:>{since.isoformat()} stars:>={TRENDING_MIN_STARS}",
         "sort": "stars", "order": "desc", "per_page": 50},
        headers,
    )
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return None

    for repo in _shuffled([r for r in items if isinstance(r, dict)]):
        name = clean(str(repo.get("full_name") or ""))
        url = str(repo.get("html_url") or "")
        if not name or not url.startswith("https://") or ledger.seen("trending", name):
            continue
        if not _unclaimed(ledger, url):
            continue

        stars = int(repo.get("stargazers_count") or 0)
        language = clean(str(repo.get("language") or ""))
        created = str(repo.get("created_at") or "")
        summary = clean(str(repo.get("description") or ""))
        age = _age(created) if created else ""
        body = phrasing.one_of(
            f"{stars} stars on a repository first pushed {age}." if age else f"{stars} stars.",
            f"Created {age} and already at {stars} stars." if age else f"At {stars} stars.",
            f"{stars} stars since it appeared{f' {age}' if age else ''}.",
        )
        if summary:
            body += f" {summary}" + ("" if summary.endswith(".") else ".")
        if language:
            body += f" Written in {language}."

        return Dispatch(
            kind="trending",
            commit_type="feat",
            emoji=phrasing.emoji_for("feat"),
            subject=f"{phrasing.verb_for('trending')} {name}",
            title=name,
            body=body,
            identifier=name,
            source_name="GitHub",
            source_url=url,
            license="Repository metadata, reported as fact",
        )
    return None


# --- docs(lobsters): what the quiet end of the internet is reading ----------------------

LOBSTERS = "https://lobste.rs/hottest.json"
LOBSTERS_FLOOR = 15


def fetch_lobsters(ledger: Ledger, today: date) -> Dispatch | None:
    stories = net.get_json(LOBSTERS)
    if not isinstance(stories, list):
        return None
    for story in _shuffled([s for s in stories if isinstance(s, dict)]):
        short_id = clean(str(story.get("short_id") or ""))
        score = int(story.get("score") or 0)
        url = str(story.get("url") or "")
        comments = str(story.get("comments_url") or "")
        if not short_id or score < LOBSTERS_FLOOR or ledger.seen("lobsters", short_id):
            continue
        # The hottest list is current by construction, so this is a guard
        # against an outlier rather than the mechanism: a story with no
        # readable date is still offered, one demonstrably old is not.
        if _stale(str(story.get("created_at") or "")):
            continue
        if not url.startswith("https://"):
            url = comments if comments.startswith("https://") else ""
        if not url or not _unclaimed(ledger, url):
            continue
        if not feeds.free_to_read(url, str(story.get("title") or "")):
            continue

        title = clean(str(story.get("title") or ""))
        tags = [clean(str(t)) for t in (story.get("tags") or []) if t]
        domain = _domain(url)
        submitter = clean(str((story.get("submitter_user") or {}).get("username") or "")) if isinstance(story.get("submitter_user"), dict) else clean(str(story.get("submitter_user") or ""))
        body = phrasing.one_of(
            f"{score} points on Lobsters, from {domain}.",
            f"From {domain}, sitting at {score} points on Lobsters.",
            f"Lobsters has it at {score} points; the source is {domain}.",
        )
        if tags:
            body += " Tagged " + ", ".join(tags[:4]) + "."
        return Dispatch(
            kind="lobsters",
            commit_type="docs",
            emoji=phrasing.emoji_for("docs"),
            subject=f"{phrasing.verb_for('lobsters')} {title}",
            title=title,
            body=body,
            identifier=short_id,
            source_name="Lobsters",
            source_url=url,
            license="Title and score, reported as fact",
            attribution=f"submitted by {submitter}" if submitter else "",
            extra_links=[("discussion", comments)] if comments.startswith("https://") else [],
        )
    return None


# --- docs(<publisher>): one entry from a syndicated source -------------------------

# How far into a feed to look, AFTER the window and the sort. Taking the
# newest entry alone would put one story on the page for as long as it led
# the feed; shuffling the whole thing would surface last fortnight's.
#
# Eight rather than twelve because of what a live feed turned out to look
# like. The Node.js blog carries a thousand entries and ships often, so
# twelve deep reached five weeks back, and the first real probe picked a
# release twenty-seven days old while the current one sat at the top of the
# same document. A page claiming the most recent developer news has to mean
# the top of the feed rather than somewhere near it.
FEED_DEPTH = 8

_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _feed_body(feed: feeds.Feed, item: feeds.Item) -> str:
    """The prose that reaches the commit and the archive.

    Longer than the aggregator bodies on purpose. An aggregator entry is a
    title and a score, and the score is the story. A publisher entry comes
    with the publisher's own summary, a byline and a filing, and dropping all
    of that would leave a headline on the page with nothing under it.
    """
    age = _age(item.published.isoformat()) if item.published else "recently"
    parts = [phrasing.one_of(
        f"{feed.name} published this {age}.",
        f"From {feed.name}, {age}.",
        f"{feed.name} ran it {age}.",
    )]
    summary = clean(item.summary)
    if summary:
        parts.append(summary if summary.endswith((".", "!", "?", "\u2026")) else summary + ".")
    else:
        # Some feeds carry headlines and nothing else, and a release blog is
        # the common case: "Node.js 26.10.0 (Current)" IS the news. Saying
        # where the detail lives beats a body that stops at the date.
        parts.append(f"The feed carries no summary; the release note is at {_domain(item.link)}.")
    author = clean(item.author)
    if author:
        parts.append(f"By {author}.")
    tags = [clean(c) for c in item.categories]
    if any(tags):
        parts.append("Filed under " + ", ".join(t for t in tags if t) + ".")
    where = _domain(item.link)
    if where and where not in feed.home:
        parts.append(f"The link goes to {where}.")
    return " ".join(parts)


def fetch_feed(feed: feeds.Feed):
    """A fetcher for one row of the table, closed over that row.

    One function, nineteen sources. Everything that differs between them is
    already data, so the alternative is the same forty lines nineteen times
    and a twentieth source nobody adds.
    """
    def fetcher(ledger: Ledger, today: date) -> Dispatch | None:
        document = net.get_text(feed.url)
        if not document:
            return None
        # Window first, then sort, then slice. Slicing before filtering
        # spends the whole budget on entries that were never eligible, which
        # is how a source with a long archive goes quiet for no reason.
        fresh = [i for i in feeds.parse(document)
                 if not (i.published and _stale(i.published.isoformat(), feed.window))]
        fresh.sort(key=lambda i: i.published or _EPOCH, reverse=True)
        top = fresh[:FEED_DEPTH]

        # NEWEST FIRST, AND NOT SHUFFLED. The aggregators shuffle because
        # their lists are a ranking: any of the front page is "what people
        # are reading", so picking at random is picking fairly. A feed is a
        # chronology, and the top of it is the news. Shuffling eight entries
        # that span six weeks, which is what the Node.js blog turned out to
        # be, meant a real probe offering a release twenty-seven days old
        # with the current one sitting above it in the same document.
        #
        # Variety does not need a shuffle here. The ledger supplies it: the
        # newest unsent entry is sent, and the next run takes the one after
        # it, until something newer arrives and goes to the top. Across
        # twenty-two sources that is more variety than any one feed could
        # give, and every entry is the most recent thing that source had to
        # say which this page had not already said.
        for item in top:
            identifier = clean(item.identifier)[:200]
            if not identifier or ledger.seen(feed.key, identifier):
                continue
            # A missing date is not an old one, so an entry the generator
            # dated badly is still offered. One demonstrably outside this
            # source's window is not.
            if not _unclaimed(ledger, item.link):
                continue
            # One entry behind the wall at a publisher that is otherwise
            # open. LWN's "[$]" is the case that got one onto the page.
            if not feeds.free_to_read(item.link, item.title, item.summary):
                continue
            title = clean(item.title)
            if not title:
                continue
            return Dispatch(
                kind=feed.key,
                commit_type=feed.commit_type,
                emoji=phrasing.emoji_for(feed.commit_type),
                subject=f"{phrasing.verb_for('release' if feed.tier == 'primary' else 'news')} {title}",
                title=title,
                body=_feed_body(feed, item),
                identifier=identifier,
                source_name=feed.name,
                source_url=item.link,
                license=feed.note,
                attribution=f"by {clean(item.author)}" if clean(item.author) else "",
                extra_links=[(feed.name, feed.home)] if _domain(item.link) not in feed.home else [],
            )
        return None

    fetcher.__name__ = f"fetch_{feed.key}"
    fetcher.__doc__ = f"One entry from {feed.name}, no older than {feed.window} days."
    return fetcher


# --- the picker -------------------------------------------------------------------

FETCHERS: dict = {
    "hn": fetch_hn,
    "trending": fetch_trending,
    "lobsters": fetch_lobsters,
    **{feed.key: fetch_feed(feed) for feed in feeds.FEEDS},
}

KINDS = tuple(FETCHERS)


def draw_order() -> list:
    """The kinds in the order they will be tried.

    An earlier design weighted this, because two kinds drew on finite lists
    that had to be rationed. Every source here keeps producing, so all of
    them are equals and the order is a plain shuffle. With twenty-two kinds a
    run almost always finds something on its first or second try, and the one
    it lands on is not the one it landed on yesterday.
    """
    return _shuffled(list(KINDS))


def pick_dispatch(ledger: Ledger, today: date) -> Dispatch | None:
    """Try each kind in turn until one yields an entry."""
    for kind in draw_order():
        try:
            entry = FETCHERS[kind](ledger, today)
        except Exception as exc:
            print(f"::warning::{kind} raised {exc!r}; trying the next kind.")
            continue
        if entry is not None:
            print(f"picked {entry.commit_type}({entry.scope}): {entry.title}")
            return entry
        print(f"{kind}: nothing available today, trying the next kind.")
    return None
