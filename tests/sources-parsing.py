# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every source adapter, against a recorded shape of what its API returns.

The fixtures are the documented formats: UnicodeData.txt's semicolon
fields, the RFC Editor's per-RFC JSON, the OEIS search
JSON, MediaWiki wikitext, SPARQL result bindings, the awesome-falsehood
list. A change to any adapter is caught here before a random moment finds
it on the page.
"""

from __future__ import annotations

import re
from datetime import date

import phrasing
import sources
from state import Ledger

TODAY = date(2026, 9, 17)
HOUSE = re.compile(r"^(?P<type>[a-z]+)\((?P<scope>[a-z0-9][a-z0-9-]*)\): (?P<subject>.+)$")


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


# --- feat(unicode) ------------------------------------------------------------

UNICODE_DATA = "\n".join([
    "0000;<control>;Cc;0;BN;;;;;N;NULL;;;;",
    "0041;LATIN CAPITAL LETTER A;Lu;0;L;;;;;N;;;;0061;",
    "200B;ZERO WIDTH SPACE;Cf;0;BN;;;;;N;;;;;",
    "2014;EM DASH;Pd;0;ON;;;;;N;;;;;",
    "2603;SNOWMAN;So;0;ON;;;;;N;;;;;",
    "4E00;<CJK Ideograph, First>;Lo;0;L;;;;;N;;;;;",
    "9FFF;<CJK Ideograph, Last>;Lo;0;L;;;;;N;;;;;",
    "1F600;GRINNING FACE;So;0;ON;;;;;N;;;;;",
])
BLOCKS = "0000..007F; Basic Latin\n2000..206F; General Punctuation\n2600..26FF; Miscellaneous Symbols\n1F600..1F64F; Emoticons\n"
AGES = "0041..005A    ; 1.1 #  [26] LATIN CAPITAL LETTER A..Z\n2014          ; 1.1 #       EM DASH\n2600..2613    ; 1.1 #  [20] ...\n1F600         ; 6.1 #       GRINNING FACE\n"


def test_unicode_picks_a_printable_named_character(repo, fake_net, seeded):
    fake_net.text(sources.UCD, UNICODE_DATA).text(sources.UCD_BLOCKS, BLOCKS).text(sources.UCD_AGE, AGES)
    led = ledger(repo)
    for used in ("0041", "1F600"):
        led.remember("unicode", used)
    entry = sources.fetch_unicode(led, TODAY)
    assert entry is not None and entry.identifier == "2603"
    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["unicode"]
    assert rest == "U+2603 ☃ SNOWMAN"
    # The heading and the subject both carry the name, so the body says what it
    # is instead, in one of several phrasings. The facts are the invariant.
    assert not entry.body.startswith("U+2603")
    for fact in ("Miscellaneous Symbols", "version 1.1", "renders as ☃",
                 "E2 98 83", "&#x2603;", "symbol"):
        assert fact in entry.body, fact
    assert_well_formed(entry)


def test_unicode_never_offers_controls_formats_or_algorithmic_names(repo, fake_net, seeded):
    fake_net.text(sources.UCD, UNICODE_DATA).text(sources.UCD_BLOCKS, BLOCKS).text(sources.UCD_AGE, AGES)
    led = ledger(repo)
    seen = set()
    for _ in range(12):
        entry = sources.fetch_unicode(led, TODAY)
        if entry is None:
            break
        seen.add(entry.identifier)
        led.remember("unicode", entry.identifier)
    assert seen == {"0041", "2603", "1F600"}  # never U+2014: the gate bans the glyph itself


def test_unicode_survives_a_missing_blocks_file(repo, fake_net, seeded):
    fake_net.text(sources.UCD, UNICODE_DATA)
    entry = sources.fetch_unicode(ledger(repo), TODAY)
    assert entry is not None and "Unassigned block" in entry.body


# --- docs(rfc) -----------------------------------------------------------------

def rfc_record(url):
    n = int(re.search(r"rfc(\d+)\.json", url).group(1))
    return {
        "doc_id": f"RFC{n:04d}", "title": f"Title Of {n} \u2014 With A Dash", "pub_date": "April 1998",
        "status": "INFORMATIONAL", "authors": ["L. Masinter"], "abstract": f"<p>The abstract of {n}.</p><p>Second &amp; last.</p>",
        "obsoletes": [], "obsoleted_by": ["RFC7168", "RFC7169"], "updates": ["RFC2068"], "updated_by": [], "page_count": "10",
    }


def test_rfc_reads_the_editor_record(repo, fake_net, seeded):
    fake_net.json("https://www.rfc-editor.org/rfc/rfc", rfc_record)
    entry = sources.fetch_rfc(ledger(repo), TODAY)
    assert entry is not None
    n = int(entry.identifier)
    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["rfc"]
    assert rest.startswith(f"RFC {n}, Title Of {n} - With A Dash")
    assert not entry.body.startswith(f"RFC {n}")
    assert "April 1998" in entry.body and "informational" in entry.body
    assert "It is obsoleted by RFC 7168 and RFC 7169; it updates RFC 2068. It runs to 10 pages." in entry.body
    assert entry.body.endswith(f"The abstract of {n}.\n\nSecond & last.") and "<p>" not in entry.body
    assert entry.attribution == "L. Masinter"
    assert entry.source_url == f"https://www.rfc-editor.org/rfc/rfc{n}"
    assert_well_formed(entry)


def test_rfc_skips_unissued_numbers_and_gives_up_cleanly(repo, fake_net, seeded):
    fake_net.json("https://www.rfc-editor.org/rfc/rfc", {"title": "Not Issued"})
    assert sources.fetch_rfc(ledger(repo), TODAY) is None


# --- test(sequence) -------------------------------------------------------------

OEIS_RECORDS = [
    {"number": 45, "data": "0,1,1,2,3,5,8,13,21,34,55", "name": "Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1."},
    {"number": 40, "data": "2,3,5,7,11,13,17,19,23,29,31", "name": "The prime numbers"},
]
OEIS = OEIS_RECORDS  # the endpoint answers a bare array, null when empty


def test_sequence_shows_eight_terms_and_answers_with_the_ninth(repo, fake_net, seeded):
    fake_net.json(sources.OEIS_SEARCH, OEIS)
    led = ledger(repo)
    led.remember("sequence", "40")
    entry = sources.fetch_sequence(led, TODAY)
    assert entry is not None and entry.identifier == "45"
    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["sequence"] and rest == "0, 1, 1, 2, 3, 5, 8, 13"
    assert entry.title == "0, 1, 1, 2, 3, 5, 8, 13, what comes next?"
    # The question is the title and the answer is the body, which the
    # page folds away so the page still poses a puzzle.
    assert entry.body == "The next term is 21. This is A000045, Fibonacci numbers: F(n) = F(n-1) + F(n-2) with F(0) = 0 and F(1) = 1."
    assert entry.spoiler is True
    assert "0, 1, 1, 2, 3, 5, 8, 13" not in entry.body
    assert entry.source_url == "https://oeis.org/A000045"
    assert_well_formed(entry)


def test_sequence_reads_the_old_envelope_and_survives_an_empty_page(repo, fake_net, seeded):
    assert sources._oeis_results({"count": 2, "results": OEIS_RECORDS}) == OEIS_RECORDS
    assert sources._oeis_results(None) == [] and sources._oeis_results(OEIS_RECORDS) == OEIS_RECORDS
    fake_net.json(sources.OEIS_SEARCH, None)  # every page empty
    assert sources.fetch_sequence(ledger(repo), TODAY) is None
    assert len(fake_net.requests) == 5


def test_sequence_appends_a_full_stop_when_the_name_lacks_one(repo, fake_net, seeded):
    fake_net.json(sources.OEIS_SEARCH, OEIS)
    led = ledger(repo)
    led.remember("sequence", "45")
    entry = sources.fetch_sequence(led, TODAY)
    assert entry is not None and entry.body.endswith("This is A000040, The prime numbers.")


# --- refactor(rosetta) ------------------------------------------------------------

WIKITEXT = """{{task}}Write a program that prints the numbers.

=={{header|COBOL}}==
<syntaxhighlight lang="cobol">
       IDENTIFICATION DIVISION.
       PROGRAM-ID. FIZZBUZZ.
</syntaxhighlight>

=={{header|Zig`x}}==
<syntaxhighlight lang="zig">
<a href="https://phish.example/">evil</a>
</syntaxhighlight>

=={{header|Python}}==
<lang python>for i in range(1, 101):
    print("FizzBuzz" if i % 15 == 0 else i)</lang>

=={{header|C sharp|C#}}==
<syntaxhighlight lang="csharp">
Console.WriteLine("hi");
</syntaxhighlight>
"""


def rosetta_net(fake_net):
    fake_net.json(sources.ROSETTA_API + "?action=query", {"query": {"categorymembers": [{"title": "FizzBuzz"}, {"title": "Sorting algorithms/Bubble sort"}]}})
    fake_net.json(sources.ROSETTA_API + "?action=parse", {"parse": {"wikitext": {"*": WIKITEXT}, "revid": 12345}})


def test_rosetta_extracts_every_solution_and_cites_the_revision(repo, fake_net, seeded):
    rosetta_net(fake_net)
    led = ledger(repo)
    seen = {}
    for _ in range(8):
        entry = sources.fetch_rosetta(led, TODAY)
        if entry is None:
            break
        led.remember("rosetta", entry.identifier)
        seen[entry.identifier] = entry
    languages = {i.split("|", 1)[1] for i in seen}
    assert {"COBOL", "Zig`x", "Python", "C sharp"} <= languages
    cobol = next(e for i, e in seen.items() if i.endswith("|COBOL"))
    # Three phrasings, and a different tail once the task has been shown
    # before, which it has by the time this loop reaches COBOL. What every
    # phrasing carries is the count and the language.
    assert "4 " in cobol.body and "COBOL" in cobol.body
    assert "Rosetta Code" in cobol.body
    assert cobol.code.startswith("       IDENTIFICATION DIVISION.")
    assert cobol.code_language == "cobol"
    assert cobol.source_url.endswith("index.php?title=FizzBuzz&oldid=12345") or "Sorting_algorithms/Bubble_sort&oldid=12345" in cobol.source_url
    assert cobol.license == "GFDL-1.2-only"
    python = next(e for i, e in seen.items() if i.endswith("|Python"))
    assert python.code_language == "python" and "print(" in python.code
    for entry in seen.values():
        assert_well_formed(entry)


def test_rosetta_revisits_a_task_in_a_new_language(repo, fake_net, seeded):
    rosetta_net(fake_net)
    led = ledger(repo)
    led.remember("rosetta", "FizzBuzz|COBOL")
    led.remember("rosetta", "Sorting algorithms/Bubble sort|COBOL")
    entry = sources.fetch_rosetta(led, TODAY)
    assert entry is not None and entry.identifier.split("|")[1] != "COBOL"
    assert entry.subject.split(" ")[0] in phrasing.VERBS["rosetta-again"]
    assert ", now in " in entry.title


def test_rosetta_can_cite_without_reproducing(repo, fake_net, seeded, monkeypatch):
    rosetta_net(fake_net)
    monkeypatch.setattr(sources, "REPRODUCE_ROSETTA_CODE", False)
    entry = sources.fetch_rosetta(ledger(repo), TODAY)
    assert entry is not None and entry.code is None and "cites rather than reproduces" in entry.body


# --- fix(bug): Wikipedia ------------------------------------------------------------

BUG_WIKITEXT = """== Space ==
* The [[Mars Climate Orbiter]] was lost in 1999 because one team used [[Pound-force|pound-force seconds]] while another used newton-seconds.<ref>{{cite web|url=x}}</ref> ''It burned up.''
** A sub-point that is not an entry.
* Short.
* [[Therac-25]] \u2014 a race condition in the control software delivered massive radiation overdoses to patients.
"""


def test_bug_reads_the_list_and_strips_the_markup(repo, fake_net, seeded):
    fake_net.json(sources.WIKIPEDIA_API, {"parse": {"wikitext": {"*": BUG_WIKITEXT}, "revid": 777}})
    led = ledger(repo)
    seen = []
    for _ in range(3):
        entry = sources.fetch_bug(led, TODAY)
        if entry is None:
            break
        led.remember("bug", entry.identifier)
        seen.append(entry)
    assert {e.title for e in seen} == {"Mars Climate Orbiter", "Therac-25"}
    orbiter = next(e for e in seen if e.title == "Mars Climate Orbiter")
    assert orbiter.body == "The Mars Climate Orbiter was lost in 1999 because one team used pound-force seconds while another used newton-seconds. It burned up."
    verb, _, rest = orbiter.subject.partition(" ")
    assert verb in phrasing.VERBS["bug"] and rest == "Mars Climate Orbiter"
    assert orbiter.source_url.endswith("oldid=777")
    assert led.retired == {"bug"}  # the third call found nothing left and retired the kind
    for entry in seen:
        assert_well_formed(entry)


# --- fix(falsehood): awesome-falsehood -----------------------------------------------

FALSEHOOD_LIST = """## Dates, Time and Time Zones

- [Falsehoods Programmers Believe About Time](https://infiniteundo.com/post/25326999628/) - A classic \u2013 with a dash.
- [Your Calendrical Fallacy Is...](https://yourcalendricalfallacyis.com) - Not matched, no falsehood in the title.
- [Falsehoods about Names](http://insecure.example/) - Rejected, not https.
"""


def test_falsehood_reads_the_list(repo, fake_net, seeded):
    fake_net.text(sources.FALSEHOOD_LIST, FALSEHOOD_LIST)
    led = ledger(repo)
    entry = sources.fetch_falsehood(led, TODAY)
    assert entry is not None
    assert entry.identifier == "https://infiniteundo.com/post/25326999628/"
    verb, _, rest = entry.subject.partition(" ")
    assert verb in phrasing.VERBS["falsehood"]
    assert rest == "what programmers believe about Time"
    assert entry.body == "A classic - with a dash."
    led.remember("falsehood", entry.identifier)
    assert sources.fetch_falsehood(led, TODAY) is None and led.retired == {"falsehood"}
    assert_well_formed(entry)


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
        return sources.Dispatch(kind="rfc", commit_type="docs", emoji="\U0001F4DD", subject="record RFC 1, Host Software", title="RFC 1", body="b", identifier="1", source_name="RFC Editor", source_url="https://www.rfc-editor.org/rfc/rfc1", license="freely reproducible",)

    monkeypatch.setattr(sources, "FETCHERS", {"a": boom, "b": empty, "c": works})
    monkeypatch.setattr(sources, "COMMON", ("a", "b", "c"))
    monkeypatch.setattr(sources, "RARE", ())
    entry = sources.pick_dispatch(ledger(repo), TODAY)
    assert entry is not None and entry.identifier == "1"
    assert set(calls) == {"boom", "empty", "works"}
