# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The syndicated sources, and a parser hard enough to point at the open internet.

WHAT COUNTS AS TRUSTED. Three tiers, and the tier is the argument rather than
a label. **Primary** is a project publishing its own release notes: there is
no intermediary to get it wrong, so a Go release announced on the Go blog is
as close to fact as technology news gets. **Registry** is a public body whose
job is the record itself. **Press** is a desk with named editors, a masthead
and a correction policy, which is what separates a publication from a feed of
opinions.

Aggregators are deliberately not here. Hacker News, Lobsters and a trending
repository list report what people are *reading*, which is a different and
also useful thing; they live in `sources.py` and are drawn from the same hat.

WHY A TABLE AND NOT NINETEEN FUNCTIONS. RSS and Atom are two shapes, not
nineteen. Everything that varies between these sources is data: a URL, a name,
a commit type, and a sentence about the terms. A function per source would be
the same forty lines nineteen times, and the twentieth source would be the one
nobody adds.

This module knows nothing about dispatches, ledgers or commits. It turns a
feed into `Item` records and stops, which is what makes it testable against a
recorded payload and what keeps `sources.py` the only place that decides what
reaches the page.
"""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from config import NEWS_WINDOW_DAYS

# --- the registry -----------------------------------------------------------------


@dataclass(frozen=True)
class Feed:
    """One syndicated source, and why it is on the page."""

    key: str  # the ledger scope and the commit scope: docs(ars)
    name: str  # what the page calls it
    url: str  # the feed itself
    home: str  # where a reader goes to check it
    tier: str  # primary, registry or press
    commit_type: str = "docs"  # docs, or security where that is what it is
    note: str = "Headline, summary and link, reported as fact"

    @property
    def window(self) -> int:
        """How old an entry may be and still count as news, for this source.

        A press desk publishes daily, so anything from last month is stale and
        the standard window applies. A language publishes when it ships, and
        Go 1.26 landing three weeks ago is still the news for anyone who has
        not upgraded. Holding both to fourteen days would take every primary
        source dark for most of the year, which would make this list a
        decoration rather than a source of anything.
        """
        return 45 if self.tier in ("primary", "registry") else NEWS_WINDOW_DAYS


# Every project here publishes its own releases, so the feed IS the source.
# Nothing sits between the announcement and the page, which is the strongest
# claim to accuracy any of these tiers can make.
PRIMARY = (
    Feed("github", "The GitHub Blog: Changelog", "https://github.blog/changelog/feed/",
         "https://github.blog/changelog/", "primary", "feat"),
    Feed("python", "Python Insider", "https://pythoninsider.blogspot.com/feeds/posts/default",
         "https://pythoninsider.blogspot.com/", "primary", "feat"),
    Feed("rust", "The Rust Blog", "https://blog.rust-lang.org/feed.xml",
         "https://blog.rust-lang.org/", "primary", "feat"),
    Feed("golang", "The Go Blog", "https://go.dev/blog/feed.atom",
         "https://go.dev/blog/", "primary", "feat"),
    Feed("node", "Node.js Blog", "https://nodejs.org/en/feed/blog.xml",
         "https://nodejs.org/en/blog/", "primary", "feat"),
    Feed("kubernetes", "Kubernetes Blog", "https://kubernetes.io/feed.xml",
         "https://kubernetes.io/blog/", "primary", "feat"),
    Feed("postgres", "PostgreSQL News", "https://www.postgresql.org/news.rss",
         "https://www.postgresql.org/about/newsarchive/", "primary", "feat"),
    Feed("mozilla", "Mozilla Hacks", "https://hacks.mozilla.org/feed/",
         "https://hacks.mozilla.org/", "primary"),
)

# A public body whose product is the record. Cited rather than reported.
REGISTRY = (
    Feed("cisa", "CISA Cybersecurity Advisories",
         "https://www.cisa.gov/cybersecurity-advisories/all.xml",
         "https://www.cisa.gov/news-events/cybersecurity-advisories", "registry", "security",
         "Advisory metadata, a work of the United States government"),
)

# Desks with named editors, a masthead and a corrections policy. That is the
# line: a publication answers for what it prints, and a feed of opinions does
# not. Each of these has been publishing technical journalism for a decade or
# more, which is the only track record worth anything here.
PRESS = (
    Feed("ars", "Ars Technica", "https://feeds.arstechnica.com/arstechnica/index",
         "https://arstechnica.com/", "press"),
    Feed("lwn", "LWN.net", "https://lwn.net/headlines/newrss",
         "https://lwn.net/", "press"),
    Feed("register", "The Register", "https://www.theregister.com/headlines.atom",
         "https://www.theregister.com/", "press"),
    Feed("spectrum", "IEEE Spectrum", "https://spectrum.ieee.org/feeds/feed.rss",
         "https://spectrum.ieee.org/", "press"),
    Feed("infoq", "InfoQ", "https://feed.infoq.com/",
         "https://www.infoq.com/", "press"),
    Feed("phoronix", "Phoronix", "https://www.phoronix.com/rss.php",
         "https://www.phoronix.com/", "press"),
    Feed("bbc", "BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml",
         "https://www.bbc.com/news/technology", "press"),
    Feed("guardian", "The Guardian Technology", "https://www.theguardian.com/uk/technology/rss",
         "https://www.theguardian.com/uk/technology", "press"),
    Feed("npr", "NPR Technology", "https://feeds.npr.org/1019/rss.xml",
         "https://www.npr.org/sections/technology/", "press"),
    Feed("verge", "The Verge", "https://www.theverge.com/rss/index.xml",
         "https://www.theverge.com/", "press"),
)

FEEDS = PRIMARY + REGISTRY + PRESS


# --- reading a feed ---------------------------------------------------------------

# A feed is a document from the open internet parsed by an XML parser, which
# is the one combination in this repository that can take the runner down
# rather than merely return nothing. A document type declaration is how both
# of the classic attacks arrive: external entities that make the parser fetch
# a file, and nested entities that expand a kilobyte into a gigabyte. None of
# these sources needs one, so a feed that carries one is not parsed at all.
# Refusing the declaration is a complete defence against both and needs no
# dependency to implement, which is the whole argument for doing it this way.
_DECLARATION = re.compile(rb"<!\s*(DOCTYPE|ENTITY)", re.IGNORECASE)

# Feeds are text. Eight megabytes is more than any of these has ever been and
# far less than the runner has, sitting under net.py's own ceiling.
MAX_FEED_BYTES = 8 * 1024 * 1024

_TAGS = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")

# A tag becomes a space, because "wrote<br>about" must not become one word.
# That leaves a space in front of whatever punctuation followed the tag, and
# a summary ending "...the Linux kernel ." is how a feed reader announces
# that it does not read what it prints. Closing punctuation comes back to
# the word it belongs to, and an opening bracket to the one after it.
_BEFORE = re.compile(r"\s+([,.;:!?%)\]}])")
_AFTER = re.compile(r"([(\[{])\s+")

# How much of a summary reaches the page. Long enough to say what happened,
# short enough that the archive stays a page of dispatches rather than a
# mirror of somebody else's article, which is also the line that keeps this
# on the right side of quoting them at all.
SUMMARY_LIMIT = 360


@dataclass(frozen=True)
class Item:
    """One entry, in the shape the two formats agree on."""

    title: str
    link: str
    summary: str = ""
    published: datetime | None = None
    author: str = ""
    categories: tuple = ()
    identifier: str = ""


def _text(node) -> str:
    """The readable text of an element, markup and entities resolved."""
    if node is None:
        return ""
    raw = "".join(node.itertext())
    flat = _SPACE.sub(" ", html.unescape(_TAGS.sub(" ", html.unescape(raw))))
    return _AFTER.sub(r"\1", _BEFORE.sub(r"\1", flat)).strip()


def _strip(name: str) -> str:
    """A tag without its namespace, because the namespace is the format."""
    return name.rsplit("}", 1)[-1].lower()


def _find(entry, *names):
    """The first child matching any of these local names."""
    wanted = {n.lower() for n in names}
    for child in entry:
        if _strip(child.tag) in wanted:
            return child
    return None


def _all(entry, *names) -> list:
    wanted = {n.lower() for n in names}
    return [c for c in entry if _strip(c.tag) in wanted]


def _moment(value: str) -> datetime | None:
    """A feed's date, in either of the two spellings the formats use.

    RSS carries RFC 822 and Atom carries RFC 3339, and a feed in the wild
    carries whichever its generator felt like. Both are tried and an
    unreadable date is None, which the caller treats as "no date" rather than
    as "old": a source that renamed a field is not a source publishing
    nothing.
    """
    value = (value or "").strip()
    if not value:
        return None
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            when = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if when is None:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def _link_of(entry) -> str:
    """The entry's canonical link, from either format's spelling of it."""
    for child in _all(entry, "link"):
        rel = (child.get("rel") or "alternate").lower()
        href = (child.get("href") or "").strip()
        if href and rel == "alternate":
            return href
        if not href and (child.text or "").strip():
            return (child.text or "").strip()
    child = _find(entry, "link")
    return ((child.get("href") if child is not None else "") or "").strip()


def _summary_of(entry) -> str:
    """The longest of the fields a feed might put a summary in, trimmed.

    Longest because the formats disagree about which field is the summary and
    which is the whole article, and the generators disagree with the formats.
    Taking the longest and trimming gives the same answer whichever it was.
    """
    parts = [_text(c) for c in _all(entry, "description", "summary", "content", "encoded", "subtitle")]
    best = max(parts, key=len, default="")
    if len(best) <= SUMMARY_LIMIT:
        return best
    cut = best[:SUMMARY_LIMIT]
    # Prefer the end of a sentence, then the end of a word, then the cut.
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if stop > SUMMARY_LIMIT // 2:
        return cut[: stop + 1]
    space = cut.rfind(" ")
    return (cut[:space] if space > SUMMARY_LIMIT // 2 else cut).rstrip(" ,;:") + "..."


def _author_of(entry) -> str:
    """Whoever the feed names, from either format's spelling."""
    node = _find(entry, "author", "creator")
    if node is None:
        return ""
    named = _find(node, "name")
    return _text(named if named is not None else node)


def _categories_of(entry) -> tuple:
    out = []
    for child in _all(entry, "category"):
        label = (child.get("term") or _text(child)).strip()
        if label and label.lower() not in {c.lower() for c in out}:
            out.append(label)
    return tuple(out[:4])


def parse(document: str | bytes) -> list:
    """Every entry in an RSS or Atom document, in the order it was published.

    Returns an empty list rather than raising for anything malformed. A source
    that changed shape overnight is an ordinary Tuesday here: the picker moves
    to the next kind, and the run that finds nothing writes nothing.
    """
    raw = document.encode("utf-8", "replace") if isinstance(document, str) else document
    if not raw or len(raw) > MAX_FEED_BYTES or _DECLARATION.search(raw[:4096]):
        return []
    try:
        root = ElementTree.fromstring(raw)  # noqa: S314 - declarations are refused above
    except ElementTree.ParseError:
        return []

    entries = [e for e in root.iter() if _strip(e.tag) in ("item", "entry")]
    items = []
    for entry in entries:
        title = _text(_find(entry, "title"))
        link = _link_of(entry)
        if not title or not link.startswith("https://"):
            continue
        stamp = _find(entry, "published", "pubdate", "updated", "date")
        identifier = _text(_find(entry, "guid", "id")) or link
        items.append(Item(
            title=title,
            link=link,
            summary=_summary_of(entry),
            published=_moment(_text(stamp)),
            author=_author_of(entry),
            categories=_categories_of(entry),
            identifier=identifier,
        ))
    return items


def by_key(key: str) -> Feed | None:
    for feed in FEEDS:
        if feed.key == key:
            return feed
    return None
