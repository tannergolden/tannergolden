# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The syndicated sources: the registry, the parser, and the fetcher over it.

The fixtures are the two formats as they are actually written, not as they are
specified. RSS dates are RFC 822 and Atom dates are RFC 3339; summaries arrive
with markup in them; a generator puts the article in `content` and a stub in
`description`. Each of those has a test, because each of them is how a feed
reader gets it wrong.

Nothing here reaches the network. The parser is a pure function over a
document, which is exactly what makes it checkable without one.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import feeds
import sources
from state import Ledger

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()
HOUSE = re.compile(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\): (?P<subject>.+)$")


def rfc822(days: float) -> str:
    return (NOW - timedelta(days=days)).strftime("%a, %d %b %Y %H:%M:%S +0000")


def rfc3339(days: float) -> str:
    return (NOW - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")


def rss(items: str) -> str:
    return f'<?xml version="1.0"?><rss version="2.0"><channel>{items}</channel></rss>'


def atom(entries: str) -> str:
    return f'<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'


# --- the registry ---------------------------------------------------------------

def test_every_source_is_named_reachable_and_accounted_for():
    """A row with a bad key takes a source dark in a way nothing else notices,
    because a fetcher that never yields looks exactly like a quiet day."""
    assert len(feeds.FEEDS) >= 19
    keys = [f.key for f in feeds.FEEDS]
    assert len(set(keys)) == len(keys), "two sources share a scope"
    for feed in feeds.FEEDS:
        # The key becomes the commit scope, which the house standard requires
        # to be a short lowercase identifier.
        assert re.fullmatch(r"[a-z0-9][a-z0-9-]*", feed.key), feed.key
        assert feed.url.startswith("https://"), feed.url
        assert feed.home.startswith("https://"), feed.home
        assert feed.tier in ("primary", "registry", "press"), feed.tier
        assert feed.commit_type in ("docs", "feat", "security"), feed.commit_type
        assert feed.note and feed.name


def test_the_three_tiers_are_all_represented():
    """The argument for trusting this page is the mix, not any one source."""
    tiers = {f.tier for f in feeds.FEEDS}
    assert tiers == {"primary", "registry", "press"}
    assert len(feeds.PRIMARY) >= 6 and len(feeds.PRESS) >= 8


def test_a_project_gets_longer_than_a_newspaper():
    """A language release from three weeks ago is still developer news. A
    technology desk's story from three weeks ago is not."""
    for feed in feeds.PRIMARY + feeds.REGISTRY:
        assert feed.window > 14
    for feed in feeds.PRESS:
        assert feed.window == 14


def test_every_feed_has_a_fetcher_in_the_picker():
    for feed in feeds.FEEDS:
        assert feed.key in sources.FETCHERS, feed.key
    assert len(sources.KINDS) == len(feeds.FEEDS) + 3


# --- the parser -----------------------------------------------------------------

def test_it_reads_rss_the_way_rss_is_written():
    document = rss(f"""
      <item>
        <title>Ars reviews the thing</title>
        <link>https://arstechnica.com/a-thing/</link>
        <description>&lt;p&gt;It is &lt;b&gt;fast&lt;/b&gt; and it is cheap.&lt;/p&gt;</description>
        <pubDate>{rfc822(1)}</pubDate>
        <category>Hardware</category><category>Reviews</category>
      </item>""")
    (item,) = feeds.parse(document)
    assert item.title == "Ars reviews the thing"
    assert item.link == "https://arstechnica.com/a-thing/"
    assert item.summary == "It is fast and it is cheap."
    assert item.categories == ("Hardware", "Reviews")
    assert (NOW - item.published).days <= 1


def test_it_reads_atom_the_way_atom_is_written():
    document = atom(f"""
      <entry>
        <title>Go 1.26 is released</title>
        <link rel="alternate" href="https://go.dev/blog/go1.26"/>
        <id>tag:go.dev,2026:go1.26</id>
        <summary type="html">&lt;p&gt;Generics get faster.&lt;/p&gt;</summary>
        <updated>{rfc3339(2)}</updated>
        <author><name>The Go Team</name></author>
        <category term="release"/>
      </entry>""")
    (item,) = feeds.parse(document)
    assert item.title == "Go 1.26 is released"
    assert item.link == "https://go.dev/blog/go1.26"
    assert item.identifier == "tag:go.dev,2026:go1.26"
    assert item.summary == "Generics get faster."
    assert item.author == "The Go Team"
    assert item.categories == ("release",)


def test_a_link_that_is_not_a_page_is_not_an_entry():
    """Every link on the page is https, including the ones somebody else chose."""
    for bad in ("http://insecure.example/x", "javascript:alert(1)", ""):
        assert feeds.parse(rss(f"<item><title>T</title><link>{bad}</link></item>")) == []
    assert feeds.parse(rss("<item><link>https://ok.example/x</link></item>")) == []


def test_the_longest_field_wins_because_the_formats_disagree():
    """A generator puts a stub in one field and the article in another, and
    which field is which is not something two of these sources agree on."""
    document = rss("""
      <item><title>T</title><link>https://x.example/a</link>
        <description>Stub.</description>
        <content:encoded xmlns:content="http://purl.org/rss/1.0/modules/content/"
          >The whole thing, which is longer than the stub by some way.</content:encoded>
      </item>""")
    (item,) = feeds.parse(document)
    assert item.summary.startswith("The whole thing")


def test_a_long_summary_is_cut_at_a_sentence():
    """Mid-word is how a feed reader looks broken; mid-sentence is how it
    looks like it is quoting somebody, which is what it is doing."""
    body = ("First sentence that runs on for a while and says something. " * 12)
    (item,) = feeds.parse(rss(
        f"<item><title>T</title><link>https://x.example/a</link>"
        f"<description>{body}</description></item>"))
    assert len(item.summary) <= feeds.SUMMARY_LIMIT + 3
    assert item.summary.endswith((".", "…", "...")), item.summary[-40:]


def test_a_date_in_either_spelling_reads_and_a_bad_one_is_not_a_date():
    assert feeds._moment(rfc822(3)) is not None
    assert feeds._moment(rfc3339(3)) is not None
    for bad in ("", "   ", "not a date", "2026-13-45"):
        assert feeds._moment(bad) is None
    # And a naive stamp is read as UTC rather than dropped.
    assert feeds._moment("2026-09-01T00:00:00").tzinfo is not None


def test_malformed_input_is_a_quiet_day_and_not_a_crash():
    for bad in ("", "not xml at all", "<rss><channel>", b"\x00\x01\x02"):
        assert feeds.parse(bad) == []


# --- the parser, pointed at the open internet -------------------------------------

def test_a_document_type_declaration_is_refused_outright():
    """The two classic XML attacks both arrive in a DOCTYPE: an external
    entity that makes the parser fetch a file, and nested entities that
    expand a kilobyte into a gigabyte. None of these sources needs one.
    """
    xxe = ('<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
           '<rss version="2.0"><channel><item><title>&xxe;</title>'
           '<link>https://x.example/a</link></item></channel></rss>')
    assert feeds.parse(xxe) == []

    billion = ('<!DOCTYPE lolz [<!ENTITY lol "lol">'
               '<!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">]>'
               '<rss><channel><item><title>&lol2;</title>'
               '<link>https://x.example/a</link></item></channel></rss>')
    assert feeds.parse(billion) == []

    # Spelled with whitespace, upper case, or on its own, it is still refused.
    for shape in ("<!DOCTYPE", "<! DOCTYPE", "<!doctype", "<!ENTITY", "<!entity"):
        assert feeds.parse(f'{shape} x><rss><channel></channel></rss>') == []


def test_a_feed_bigger_than_any_feed_is_not_parsed():
    assert feeds.parse(b"<rss>" + b"x" * (feeds.MAX_FEED_BYTES + 1)) == []


def test_markup_in_a_title_cannot_reach_the_page():
    """Nothing here is trusted, and the parser is the first place it is not."""
    (item,) = feeds.parse(rss(
        "<item><title>&lt;script&gt;alert(1)&lt;/script&gt; Real headline</title>"
        "<link>https://x.example/a</link></item>"))
    assert "<script>" not in item.title and "alert(1)" in item.title
    assert "<" not in item.title and ">" not in item.title


# --- the fetcher over one source --------------------------------------------------

ARS = feeds.by_key("ars")
GO = feeds.by_key("golang")


def one_entry(days: float = 1.0, **over) -> str:
    fields = {
        "title": "A thing happened",
        "link": "https://arstechnica.com/a-thing/",
        "summary": "Somebody shipped something and here is what it does.",
        "author": "A Reporter",
        "category": "Policy",
    }
    fields.update(over)
    return rss(f"""
      <item>
        <title>{fields['title']}</title>
        <link>{fields['link']}</link>
        <description>{fields['summary']}</description>
        <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">{fields['author']}</dc:creator>
        <category>{fields['category']}</category>
        <pubDate>{rfc822(days)}</pubDate>
      </item>""")


def test_a_syndicated_dispatch_is_detailed(repo, fake_net, seeded):
    """A headline with nothing under it is a link, not a dispatch."""
    fake_net.text(ARS.url, one_entry())
    entry = sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY)
    assert entry is not None

    from render import commit_message
    from text import is_clean
    header = commit_message(entry).split("\n", 1)[0]
    assert HOUSE.match(header) and len(header) <= 72, header
    assert is_clean(commit_message(entry))

    assert entry.kind == "ars" and entry.commit_type == "docs"
    assert entry.title == "A thing happened"
    assert entry.source_name == "Ars Technica"
    assert entry.source_url == "https://arstechnica.com/a-thing/"
    # The publisher's own words, the byline, the filing and the age.
    assert "Somebody shipped something" in entry.body
    assert "By A Reporter." in entry.body
    assert "Filed under Policy." in entry.body
    assert "Ars Technica" in entry.body
    # A floor rather than a target: the real length comes from the
    # publisher's summary, which in production runs to forty words or more.
    # This catches a body that lost its summary, not one that is terse.
    assert len(entry.body.split()) >= 15, entry.body


def test_a_source_that_gives_no_summary_still_gives_a_dispatch(repo, fake_net, seeded):
    """Some feeds carry headlines and nothing else. That is still news, and
    the body still has to say where it came from and when."""
    fake_net.text(ARS.url, rss(
        f"<item><title>Just a headline</title>"
        f"<link>https://arstechnica.com/x</link><pubDate>{rfc822(0.5)}</pubDate></item>"))
    entry = sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY)
    assert entry is not None
    assert "Ars Technica" in entry.body and "today" in entry.body
    assert entry.body.endswith(".")


def test_a_release_reads_as_a_release_and_not_as_reporting(repo, fake_net, seeded):
    fake_net.text(GO.url, one_entry(title="Go 1.26 is released",
                                    link="https://go.dev/blog/go1.26"))
    entry = sources.FETCHERS["golang"](Ledger("state/ledger.json"), TODAY)
    assert entry is not None
    assert entry.commit_type == "feat"
    import phrasing
    assert entry.subject.split(" ")[0] in phrasing.VERBS["release"]


def test_an_entry_past_its_source_window_is_not_news(repo, fake_net, seeded):
    fake_net.text(ARS.url, one_entry(days=ARS.window + 2))
    assert sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY) is None

    # The same age from a project is still news, because it publishes on
    # release rather than daily.
    fake_net.text(GO.url, one_entry(days=ARS.window + 2, link="https://go.dev/blog/x"))
    assert sources.FETCHERS["golang"](Ledger("state/ledger.json"), TODAY) is not None


def test_an_entry_with_no_readable_date_is_still_offered(repo, fake_net, seeded):
    """A source that renamed a field is not a source publishing nothing."""
    fake_net.text(ARS.url, rss(
        "<item><title>T</title><link>https://arstechnica.com/x</link>"
        "<description>Something.</description><pubDate>garbage</pubDate></item>"))
    entry = sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY)
    assert entry is not None and "recently" in entry.body


def test_a_source_that_is_down_is_an_ordinary_tuesday(repo, fake_net, seeded):
    assert sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY) is None
    fake_net.text(ARS.url, "")
    assert sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY) is None


def test_the_same_entry_is_sent_once(repo, fake_net, seeded):
    fake_net.text(ARS.url, one_entry())
    led = Ledger("state/ledger.json")
    first = sources.FETCHERS["ars"](led, TODAY)
    assert first is not None
    led.remember("ars", first.identifier)
    assert sources.FETCHERS["ars"](led, TODAY) is None


def test_a_story_a_publisher_and_an_aggregator_both_carry_is_sent_once(repo, fake_net, seeded):
    """Ars publishes it, Hacker News links it, and the page runs it once."""
    shared = "https://arstechnica.com/a-thing/"
    fake_net.text(ARS.url, one_entry(link=shared))
    led = Ledger("state/ledger.json")
    entry = sources.FETCHERS["ars"](led, TODAY)
    assert entry is not None
    sources.claim_link(led, entry.source_url)
    assert sources.FETCHERS["ars"](led, TODAY) is None
    assert not sources._unclaimed(led, shared + "?utm_source=hn")


def test_the_newest_unsent_entry_is_the_one_that_goes(repo, fake_net, seeded):
    """A feed is a chronology, not a ranking. The aggregators shuffle because
    any of the front page is "what people are reading"; the top of a feed is
    the news, and anything else is not the most recent thing that source had
    to say.

    This is the defect a live probe found: shuffling eight entries that
    spanned six weeks offered a Node.js release twenty-seven days old with
    the current one sitting above it in the same document.
    """
    items = "".join(
        f"<item><title>Story {n}</title><link>https://arstechnica.com/s{n}</link>"
        f"<description>Number {n}.</description><pubDate>{rfc822(n)}</pubDate></item>"
        for n in range(1, 7))
    fake_net.text(ARS.url, rss(items))

    led = Ledger("state/ledger.json")
    sent = []
    for _ in range(3):
        entry = sources.FETCHERS["ars"](led, TODAY)
        assert entry is not None
        sent.append(entry.title)
        led.remember("ars", entry.identifier)
        sources.claim_link(led, entry.source_url)
    assert sent == ["Story 1", "Story 2", "Story 3"], sent


def test_the_window_is_applied_before_the_depth_and_not_after(repo, fake_net, seeded):
    """Slicing first spends the whole budget on entries that were never
    eligible, which is how a source with a long archive goes quiet."""
    old = "".join(
        f"<item><title>Ancient {n}</title><link>https://arstechnica.com/old{n}</link>"
        f"<description>Old.</description><pubDate>{rfc822(400 + n)}</pubDate></item>"
        for n in range(sources.FEED_DEPTH + 4))
    current = (f"<item><title>Today</title><link>https://arstechnica.com/new</link>"
               f"<description>New.</description><pubDate>{rfc822(0.2)}</pubDate></item>")
    fake_net.text(ARS.url, rss(old + current))

    entry = sources.FETCHERS["ars"](Ledger("state/ledger.json"), TODAY)
    assert entry is not None and entry.title == "Today"
