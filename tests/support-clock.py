# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The support clock: what it asks for, what it believes, and how it counts.

The clock's whole claim is that nobody typed any of it. These tests hold that
claim up: the languages come from the account, the dates come from the
catalogue, and the countdown is arithmetic on today rather than a sentence
somebody wrote down once.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

import pytest

import render
import support

API = "https://endoflife.date/api/"
REPOS = "https://api.github.com/users/tannergolden/repos"
TODAY = date(2026, 9, 23)
MOMENT = datetime(2026, 9, 23, 17, 5, tzinfo=timezone.utc)


def cycles(*rows):
    return list(rows)


def cycle(name, latest=None, eol=None, released="2026-09-01"):
    body = {"cycle": name, "latest": latest or name, "latestReleaseDate": released}
    if eol is not None:
        body["eol"] = eol
    return body


# --- reading the catalogue ----------------------------------------------------------

def test_the_newest_supported_line_wins_not_the_newest_line(fake_net):
    """A cycle that has gone end of life is skipped, however new it is.

    endoflife.date lists a cycle the day it is announced and keeps it after
    it dies. Taking the first row would put a dead version on a page whose
    entire point is telling a reader which one is alive.
    """
    fake_net.json(API + "python", cycles(
        cycle("3.15", "3.15.0", eol="2026-01-01"),   # newest, already dead
        cycle("3.14", "3.14.1", eol="2030-10-31"),
        cycle("3.13", "3.13.9", eol="2029-10-31"),
    ))
    found = support.fetch("Python", "python")
    assert (found.cycle, found.latest) == ("3.14", "3.14.1")
    assert found.ends == date(2030, 10, 31)


def test_end_of_life_is_spelled_three_ways_and_two_of_them_mean_supported(fake_net):
    fake_net.json(API + "a", cycles(cycle("1", eol=False)))
    fake_net.json(API + "b", cycles(cycle("2")))
    fake_net.json(API + "c", cycles(cycle("3", eol=True), cycle("2", eol="2099-01-01")))
    assert support.fetch("A", "a").forever is True
    assert support.fetch("B", "b").forever is True
    assert support.fetch("C", "c").cycle == "2"


def test_a_line_that_died_today_is_not_still_supported(fake_net, monkeypatch):
    """The boundary, pinned: eol is the last day, so today is still covered."""
    fake_net.json(API + "x", cycles(cycle("9", eol="2026-09-23"), cycle("8", eol="2027-01-01")))
    assert support.fetch("X", "x").cycle == "9"
    fake_net.json(API + "y", cycles(cycle("9", eol="2026-09-22"), cycle("8", eol="2027-01-01")))
    assert support.fetch("Y", "y").cycle == "8"


def test_a_product_that_is_not_in_the_catalogue_is_simply_absent(fake_net):
    """404 is an ordinary answer. The mapping table leans generous because of it."""
    assert support.fetch("Nothing", "nothing-at-all") is None


@pytest.mark.parametrize("payload", [{"cycles": []}, [], ["3.14"], [None], "3.14"])
def test_a_catalogue_that_changed_shape_answers_nothing_rather_than_guessing(fake_net, payload):
    fake_net.json(API + "odd", payload)
    assert support.fetch("Odd", "odd") is None


def test_every_row_carries_the_page_it_came_from(fake_net):
    fake_net.json(API + "go", cycles(cycle("1.26", "1.26.2", eol=False)))
    assert support.fetch("Go", "go").row()["url"] == "https://endoflife.date/go"


def test_dates_are_stored_as_dates_never_as_the_sentence_they_become(fake_net):
    """The countdown has to shorten on a day nothing was fetched.

    Storing "4 years left" would freeze the clock between refreshes, which is
    the one failure a thing called a clock cannot have.
    """
    fake_net.json(API + "rust", cycles(cycle("1.99", "1.99.0", eol="2027-03-01")))
    row = support.fetch("Rust", "rust").row()
    assert row["ends"] == "2027-03-01" and row["forever"] is False
    assert json.loads(json.dumps(row)) == row  # it survives the round trip to state


# --- reading the account ------------------------------------------------------------

def repo(name, language_bytes, **flags):
    return {
        "name": name,
        "fork": flags.get("fork", False),
        "archived": flags.get("archived", False),
        "languages_url": f"https://api.github.com/repos/tannergolden/{name}/languages",
        "_languages": language_bytes,
    }


def account(fake_net, *repos):
    fake_net.json(REPOS, [{k: v for k, v in r.items() if k != "_languages"} for r in repos])
    for r in repos:
        fake_net.json(r["languages_url"], r["_languages"])
    return fake_net


def test_the_languages_are_the_account_s_own_not_a_list_somebody_typed(fake_net):
    account(
        fake_net,
        repo("one", {"Python": 90_000, "Shell": 9_000}),
        repo("two", {"Python": 10_000, "JavaScript": 4_000}),
    )
    assert support.profile_languages("tannergolden", None) == ["Python", "Shell", "JavaScript"]


def test_a_fork_reports_somebody_else_s_language_and_an_archive_reports_a_past_one(fake_net):
    account(
        fake_net,
        repo("mine", {"Python": 50_000}),
        repo("theirs", {"Haskell": 900_000}, fork=True),
        repo("retired", {"Perl": 800_000}, archived=True),
    )
    assert support.profile_languages("tannergolden", None) == ["Python"]


def test_a_config_file_somebody_committed_once_is_not_a_language_this_account_writes(fake_net):
    account(fake_net, repo("one", {"Python": 50_000, "Ruby": support.MIN_BYTES - 1}))
    assert support.profile_languages("tannergolden", None) == ["Python"]


def test_an_account_the_api_will_not_talk_about_yields_no_languages_not_an_error(fake_net):
    assert support.profile_languages("tannergolden", None) == []


def test_a_languages_url_pointing_somewhere_other_than_github_is_not_followed(fake_net):
    """The field is read off a JSON body. It is a URL this code would fetch."""
    rogue = repo("evil", {})
    rogue["languages_url"] = "https://example.invalid/languages"
    fake_net.json(REPOS, [{k: v for k, v in rogue.items() if k != "_languages"}])
    fake_net.json("https://example.invalid/", {"Python": 999_999})
    assert support.profile_languages("tannergolden", None) == []
    assert not any("example.invalid" in url for url in fake_net.requests)


def test_two_languages_sharing_a_runtime_ask_about_it_once(fake_net):
    assert support.runtimes_for(["C#", "F#"]) == [(".NET", "dotnet")]
    assert support.runtimes_for(["JavaScript", "TypeScript"]) == [
        ("Node.js", "nodejs"), ("TypeScript", "typescript")]


def test_a_row_is_named_after_the_runtime_because_that_is_what_the_date_describes():
    """"Shell 5.3" linking to Bash makes the reader work out the mapping."""
    assert support.runtimes_for(["Shell"]) == [("Bash", "bash")]
    assert support.runtimes_for(["JavaScript"]) == [("Node.js", "nodejs")]
    assert support.runtimes_for(["Python"]) == [("Python", "python")]


def test_a_language_with_no_support_lifecycle_is_skipped_rather_than_guessed_at(fake_net):
    assert support.runtimes_for(["Makefile", "HTML", "CSS"]) == []


def test_no_language_is_both_mapped_to_a_runtime_and_declared_to_have_none():
    assert not (set(support.RUNTIMES) & support.NO_LIFECYCLE)


def test_the_table_cannot_grow_without_bound(fake_net):
    many = [name for name, (_, slug) in support.RUNTIMES.items() if slug != "dotnet"]
    assert len(support.runtimes_for(many)) == support.MAX_LANGUAGES


# --- the whole clock ----------------------------------------------------------------

def test_the_platforms_come_first_then_the_languages_by_bytes(fake_net):
    for _, product in support.PLATFORMS:
        fake_net.json(API + product, cycles(cycle("1", eol=False)))
    fake_net.json(API + "python", cycles(cycle("3.14", "3.14.1", eol="2030-10-31")))
    fake_net.json(API + "bash", cycles(cycle("5.3", "5.3.0", eol=False)))
    account(fake_net, repo("one", {"Python": 90_000, "Shell": 9_000, "Makefile": 5_000}))

    names = [row["name"] for row in support.collect("tannergolden", None)]
    assert names == ["macOS", "Windows", "Linux kernel", "Python", "Bash"]


def test_the_three_operating_systems_the_user_asked_for_are_always_asked_about():
    assert [name for name, _ in support.PLATFORMS] == ["macOS", "Windows", "Linux kernel"]
    assert [slug for _, slug in support.PLATFORMS] == ["macos", "windows", "linux"]


def test_a_catalogue_that_is_entirely_down_yields_nothing_rather_than_a_half_table(fake_net):
    account(fake_net, repo("one", {"Python": 90_000}))
    assert support.collect("tannergolden", None) == []


# --- the countdown ------------------------------------------------------------------

@pytest.mark.parametrize(("days", "said"), [
    (0, "0 days"), (1, "1 day"), (2, "2 days"), (59, "59 days"),
    (60, "2 months"), (180, "6 months"), (365, "12 months"), (700, "23 months"),
    (731, "2 years"), (1_503, "4 years"), (3_653, "10 years"),
])
def test_a_duration_is_said_the_way_a_person_would_say_it(days, said):
    assert render.span(days) == said


def test_the_countdown_is_arithmetic_on_today_not_a_stored_sentence():
    row = {"ends": "2026-11-02", "forever": False}
    assert "40 days left" in render.support_clock(row, TODAY)
    assert "39 days left" in render.support_clock(row, date(2026, 9, 24))


@pytest.mark.parametrize(("ends", "dot"), [
    ("2030-10-31", "\U0001F7E2"),   # years out: nothing to do
    ("2027-03-23", "\U0001F7E2"),   # six months and a day: still green
    ("2027-03-22", "\U0001F7E1"),   # six months exactly: start planning
    ("2026-09-23", "\U0001F534"),   # today
    ("2026-04-01", "\U0001F534"),   # past
])
def test_the_colour_is_the_warning_and_it_is_computed_not_chosen(ends, dot):
    assert render.support_clock({"ends": ends, "forever": False}, TODAY).startswith(dot)


def test_a_line_with_no_announced_end_says_so_rather_than_implying_forever():
    assert render.support_clock({"forever": True, "ends": None}, TODAY) == "\U0001F7E2 No end announced"
    assert render.support_clock({"forever": False, "ends": None}, TODAY) == "\U0001F7E2 No end announced"
    assert render.support_clock({"ends": "not a date"}, TODAY) == "\U0001F7E2 No end announced"


def test_a_date_that_has_passed_reads_as_news_not_as_a_countdown():
    said = render.support_clock({"ends": "2026-04-01", "forever": False}, TODAY)
    assert said == "\U0001F534 Ended April 1, 2026 · 6 months ago"


# --- the region ---------------------------------------------------------------------

def test_the_region_is_a_table_a_reader_can_act_on():
    rows = [{"name": "Python", "url": "https://endoflife.date/python", "cycle": "3.14",
             "latest": "3.14.1", "ends": "2030-10-31", "forever": False}]
    drawn = render.render_support_region(rows, MOMENT)
    assert "| Runtime | Line | Latest | Security support ends |" in drawn
    assert "| [Python](https://endoflife.date/python) | `3.14` | `3.14.1` |" in drawn
    assert "October 31, 2030 · 4 years left" in drawn
    assert "endoflife.date" in drawn and "CC BY-SA 4.0" in drawn


def test_an_empty_clock_says_it_is_waiting_rather_than_drawing_an_empty_table():
    assert render.render_support_region([], MOMENT) == "_The support clock fills in on the first refresh._"


def test_a_name_from_the_catalogue_cannot_break_out_of_its_cell():
    rows = [{"name": "Py|thon **x**", "url": "https://endoflife.date/py", "cycle": "3|14",
             "latest": "1", "ends": None, "forever": True}]
    (body,) = [line for line in render.render_support_region(rows, MOMENT).splitlines()
               if line.startswith("| [")]
    assert len(re.findall(r"(?<!\\)\|", body)) == 5  # four cells, not six
    assert "**x**" not in body and "`3|14`" not in body


@pytest.mark.parametrize(("raw", "shown"), [
    ("3.14.1", "`3.14.1`"), ("11 25H2", "`11 25H2`"), ("1.26.2-rc1", "`1.26.2-rc1`"),
    ("6.12", "`6.12`"), ("10.0.26200", "`10.0.26200`"),
    ("`x` **b**", "`x b`"), ("a|b", "`ab`"), ("", "\u2014"), ("!!!", "\u2014"),
    ("v" * 40, "`" + "v" * 24 + "`"),
])
def test_a_version_cell_says_the_version_and_can_say_nothing_else(raw, shown):
    assert render.version_cell(raw) == shown


@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "https://endoflife.date.evil.test/x", "", "/relative",
    "HTTPS://endoflife.date/x", "http://endoflife.date/x",
])
def test_a_row_links_to_the_catalogue_or_does_not_link_at_all(url):
    """safe_url escapes a Markdown break-out. It does not judge a scheme.

    The stored URL is written by this repository, so this is not a live
    vector; it is the guard that keeps it from becoming one the day somebody
    decides the row should carry a link the source supplied.
    """
    rows = [{"name": "Thing", "url": url, "cycle": "1", "latest": "1", "forever": True}]
    drawn = render.render_support_region(rows, MOMENT)
    assert "| Thing |" in drawn and "](" not in drawn.split("\n")[2]


def test_the_reading_survives_a_day_the_catalogue_could_not_be_read(repo):
    """The page is drawn from state, so a timeout costs freshness, not the table."""
    render.save_support([{"name": "Go", "url": "https://endoflife.date/go", "cycle": "1.26",
                          "latest": "1.26.2", "ends": "2027-02-01", "forever": False}])
    assert [row["name"] for row in render.load_support()] == ["Go"]


@pytest.mark.parametrize("junk", ['{"not": "a list"}', "[1, 2, 3]", "not json at all", ""])
def test_a_state_file_that_is_not_a_clock_reads_as_no_clock(repo, junk):
    (repo / "state").mkdir(exist_ok=True)
    (repo / render.SUPPORT_FILE).write_text(junk, encoding="utf-8")
    assert render.load_support() == []


# --- the refresh ---------------------------------------------------------------------

def refresh(repo, monkeypatch, answer):
    """Run a page refresh with the catalogue answering `answer`, nothing else live."""
    import dispatches
    import modules
    from state import Ledger

    monkeypatch.setattr(modules, "terminal_tip", lambda ledger: None)
    monkeypatch.setattr(dispatches, "render_page", lambda *a, **k: None)
    monkeypatch.setattr(support, "refresh", lambda: answer)
    message = dispatches.refresh_page(Ledger(str(repo / "state/ledger.json")), MOMENT)
    # The body wraps at 72 and picks one of three phrasings, so the phrase
    # can land across a line break. Match the words, not the typography.
    return " ".join(message.lower().split())


LAST = [{"name": "Go", "product": "go", "url": "https://endoflife.date/go",
         "cycle": "1.26", "latest": "1.26.2", "ends": "2027-02-01", "forever": False}]


def test_a_refresh_that_reads_the_catalogue_records_it(repo, monkeypatch):
    message = refresh(repo, monkeypatch, LAST)
    assert render.load_support() == LAST
    assert "the support clock" in message


def test_a_refresh_that_cannot_reach_the_catalogue_keeps_the_last_reading(repo, monkeypatch):
    """One timeout costs the page a day of freshness, not its table."""
    render.save_support(LAST)
    message = refresh(repo, monkeypatch, [])
    assert render.load_support() == LAST
    assert "the support clock" not in message


def test_a_reading_that_did_not_move_is_not_reported_as_a_change(repo, monkeypatch):
    """Most days nothing ships. The commit body should not claim otherwise."""
    render.save_support(LAST)
    assert "the support clock" not in refresh(repo, monkeypatch, LAST)
    assert "the support clock" in refresh(repo, monkeypatch, [dict(LAST[0], latest="1.26.3")])


# --- the documentation ---------------------------------------------------------------

def test_the_documentation_still_describes_the_clock_that_exists():
    """How-It-Works.md is quoted. Its quotable parts are pinned to the code.

    A number in prose that nobody verifies is a number that is wrong within
    a week of somebody tuning a constant.
    """
    from pathlib import Path

    doc = Path(__file__).resolve().parent.parent.joinpath("How-It-Works.md").read_text("utf-8")
    kilobytes = support.MIN_BYTES // 1000
    # Prose spells the small numbers, so the check has to as well, or it pins
    # nothing a reader would ever see.
    spelled = {3: "three", 6: "six", 12: "twelve"}
    expected = {
        "the platforms": ", ".join(f"**{name.split()[0]}**" for name, _ in support.PLATFORMS[:2]),
        "the floor": f"above {kilobytes} KB",
        "the warning window": f"inside {spelled[render.SUPPORT_WARNING_DAYS // 30]} months",
        "the mapping it names": "JavaScript asks about Node",
        "the attribution": "CC BY-SA 4.0",
    }
    assert {name: phrase for name, phrase in expected.items() if phrase not in doc} == {}


def test_the_notice_names_every_source_the_clock_reads():
    from pathlib import Path

    notice = Path(__file__).resolve().parent.parent.joinpath("NOTICE").read_text("utf-8")
    assert "endoflife.date" in notice and "CC BY-SA 4.0" in notice
