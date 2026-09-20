# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The journal file, its frontmatter, the rolling index and the page rows."""

from __future__ import annotations

import re
from pathlib import Path

from render import (
    append_journal,
    entries_this_month,
    journal_path,
    load_recent,
    record_recent,
    render_journal_region,
    render_modules_region,
)
from sources import Entry


def make_entry(**overrides) -> Entry:
    base = dict(
        kind="unicode", commit_type="feat", emoji="✨", subject="add U+2603 ☃ SNOWMAN",
        title="U+2603 ☃ SNOWMAN", body="U+2603 is SNOWMAN \u2014 in Miscellaneous Symbols.",
        identifier="2603", source_name="Unicode Character Database",
        source_url="https://util.unicode.org/UnicodeJsps/character.jsp?a=2603", license="Unicode-3.0",
    )
    base.update(overrides)
    return Entry(**base)


def test_month_file_gets_frontmatter_with_four_tags(repo, moment):
    path = append_journal(make_entry(), moment)
    assert path == "journal/2026/09.md" == journal_path(moment)
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith("<!--\ntitle: '\U0001F4D3 JOURNAL, September 2026'")
    tags = re.search(r"^tags: \[(.+)\]$", text, flags=re.MULTILINE).group(1).split(",")
    assert len(tags) == 4
    assert "<!-- markdownlint-disable MD041 -->" in text
    assert "### 13:05 EDT · `feat(unicode)`" in text
    assert "\u2014" not in text


def test_second_entry_is_appended_not_rewritten(repo, moment):
    append_journal(make_entry(), moment)
    first = Path("journal/2026/09.md").read_text(encoding="utf-8")
    append_journal(make_entry(kind="rfc", commit_type="docs", identifier="2324", title="RFC 2324", subject="record RFC 2324", body="x"), moment)
    second = Path("journal/2026/09.md").read_text(encoding="utf-8")
    assert second.startswith(first)


def test_code_entry_is_fenced_and_attributed(repo, moment):
    entry = make_entry(kind="rosetta", commit_type="refactor", code="print('hi') ```", code_language="python", license="GFDL-1.2-only", attribution="Rosetta Code contributors")
    append_journal(entry, moment)
    text = Path("journal/2026/09.md").read_text(encoding="utf-8")
    assert "\n````python\nprint('hi') ```\n````\n" in text
    assert "License: GFDL-1.2-only" in text and "Rosetta Code contributors" in text


def test_recent_index_and_page_rows(repo, moment):
    for i in range(15):
        e = make_entry(identifier=str(i), title=f"entry {i}")
        path = append_journal(e, moment)
        record_recent(e, moment, path)
    recent = load_recent()
    assert recent[0]["title"] == "entry 14"
    assert entries_this_month(moment) == 15
    region = render_journal_region(recent, moment, 15)
    assert region.startswith("### Sunday, September 20, 2026")
    assert region.count("| 13:05 |") == 13  # 3 visible + 10 collapsed
    assert "<details>" in region and "15 entries in September" in region
    assert "assets/badges/dynamic/journal.svg" in region


def test_empty_state_renders_a_sentence_not_a_hole(repo, moment):
    region = render_journal_region([], moment, 0)
    assert "No entries yet" in region
    assert render_modules_region({}) == "_The daily modules fill in on the first refresh._"


def test_modules_render_with_escaping(repo):
    region = render_modules_region({
        "hn": {"title": "A | pipe <b>", "url": "https://x.example/", "points": 12, "domain": "x.example", "discussion": "https://news.ycombinator.com/item?id=1"},
        "tip": {"command": "jq", "description": "pull one field", "example": "jq '.a'", "url": "https://tldr.example/jq"},
    })
    assert "A \\| pipe &lt;b>" in region
    assert "> [!TIP]" in region and "> jq '.a'" in region


def test_journal_prose_cannot_become_structure(repo, moment):
    entry = make_entry(title="U+005D ] RIGHT SQUARE BRACKET", body="# not a heading\n\n- not a list\n\n[not](a-link)")
    append_journal(entry, moment)
    text = Path("journal/2026/09.md").read_text(encoding="utf-8")
    assert "**U+005D \\] RIGHT SQUARE BRACKET**" in text
    assert "\n\\# not a heading\n" in text and "\n\\- not a list\n" in text and "\\[not](a-link)" in text


def test_tip_example_cannot_close_its_own_fence(repo):
    region = render_modules_region({
        "tip": {"command": "x", "description": "d", "example": "echo ``` done", "url": "https://tldr.example/x"},
    })
    assert "> ````bash\n> echo ``` done\n> ````" in region
    assert not any(line.endswith("  ") for line in region.splitlines() if line.startswith(">"))


def test_month_badge_links_to_the_archive_before_the_first_entry(repo, moment):
    assert "(journal/)" in render_journal_region([], moment, 0)
    assert "(journal/2026/09.md)" in render_journal_region([], moment, 3)
