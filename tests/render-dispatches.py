# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The month file, its frontmatter, the rolling index and the page rows."""

from __future__ import annotations

import re
from pathlib import Path

from render import (
    append_dispatch,
    dispatch_path,
    dispatches_this_month,
    load_recent,
    record_recent,
    render_dispatches_region,
    render_modules_region,
)
from sources import Dispatch


def make_entry(**overrides) -> Dispatch:
    base = dict(
        kind="unicode", commit_type="feat", emoji="✨", subject="add U+2603 ☃ SNOWMAN",
        title="U+2603 ☃ SNOWMAN", body="U+2603 is SNOWMAN \u2014 in Miscellaneous Symbols.",
        identifier="2603", source_name="Unicode Character Database",
        source_url="https://util.unicode.org/UnicodeJsps/character.jsp?a=2603", license="Unicode-3.0",
    )
    base.update(overrides)
    return Dispatch(**base)


def test_month_file_gets_frontmatter_with_four_tags(repo, moment):
    path = append_dispatch(make_entry(), moment)
    assert path == "dispatches/2026/September.md" == dispatch_path(moment)
    text = Path(path).read_text(encoding="utf-8")
    assert text.startswith("<!--\ntitle: '\U0001F4E1 DISPATCHES, September 2026'")
    tags = re.search(r"^tags: \[(.+)\]$", text, flags=re.MULTILINE).group(1).split(",")
    assert len(tags) == 4
    assert "<!-- markdownlint-disable MD041 -->" in text
    assert "## Sunday, September 20, 2026\n\n" in text  # the day, written once
    assert "### ✨ U+2603 ☃ SNOWMAN" in text  # the heading is the entry
    assert "\n`feat(unicode)` · 13:05 EDT\n" in text
    assert "\u2014" not in text


def test_second_entry_is_appended_not_rewritten(repo, moment):
    append_dispatch(make_entry(), moment)
    first = Path("dispatches/2026/September.md").read_text(encoding="utf-8")
    append_dispatch(make_entry(kind="rfc", commit_type="docs", identifier="2324", title="RFC 2324", subject="record RFC 2324", body="x"), moment)
    second = Path("dispatches/2026/September.md").read_text(encoding="utf-8")
    assert second.startswith(first)


def test_a_backtick_in_the_language_cannot_break_the_fence(repo, moment):
    hostile = "<a href=\"https://phish.example/\">verify</a>\n## injected\n[x](https://phish.example)"
    entry = make_entry(kind="rosetta", commit_type="refactor", code=hostile, code_language="Zig`x", license="GFDL-1.2-only")
    append_dispatch(entry, moment)
    text = Path("dispatches/2026/September.md").read_text(encoding="utf-8")
    assert "\n```zigx\n" + hostile + "\n```\n" in text
    assert "```Zig`x" not in text


def test_code_entry_is_fenced_and_attributed(repo, moment):
    entry = make_entry(kind="rosetta", commit_type="refactor", code="print('hi') ```", code_language="python", license="GFDL-1.2-only", attribution="Rosetta Code contributors")
    append_dispatch(entry, moment)
    text = Path("dispatches/2026/September.md").read_text(encoding="utf-8")
    assert "\n````python\nprint('hi') ```\n````\n" in text
    assert text.rstrip().endswith("· Rosetta Code contributors · GFDL-1.2-only_\n\n---")


def test_recent_index_and_page_rows(repo, moment):
    Path("assets/badges/dynamic").mkdir(parents=True)
    for name in ("dispatches", "month"):
        Path(f"assets/badges/dynamic/{name}.svg").write_text(f"<svg>{name}</svg>", encoding="utf-8")
    for i in range(15):
        e = make_entry(identifier=str(i), title=f"entry {i}")
        path = append_dispatch(e, moment)
        record_recent(e, moment, path)
    recent = load_recent()
    assert recent[0]["title"] == "entry 14"
    assert dispatches_this_month(moment) == 15
    region = render_dispatches_region(recent, moment, 15)
    assert region.startswith("### Sunday, September 20, 2026")
    assert region.count("| 13:05 |") == 13  # 3 visible + 10 collapsed
    assert "<details>" in region and "15 in September" in region
    assert re.search(r"assets/badges/dynamic/dispatches\.svg\?v=[0-9a-f]{8}\)", region)
    assert re.search(r"assets/badges/dynamic/month\.svg\?v=[0-9a-f]{8}\)", region)


def test_empty_state_renders_a_sentence_not_a_hole(repo, moment):
    region = render_dispatches_region([], moment, 0)
    assert "No dispatches yet" in region
    assert render_modules_region({}) == "_The daily modules fill in on the first refresh._"


def test_modules_render_with_escaping(repo):
    region = render_modules_region({
        "hn": {"title": "A | pipe <b>", "url": "https://x.example/", "points": 12, "domain": "x.example", "discussion": "https://news.ycombinator.com/item?id=1"},
        "tip": {"command": "jq", "description": "pull one field", "example": "jq '.a'", "url": "https://tldr.example/jq"},
    })
    assert "A \\| pipe &lt;b>" in region
    assert "> [!TIP]" in region and "> jq '.a'" in region


def test_dispatch_prose_cannot_become_structure(repo, moment):
    entry = make_entry(title="U+005D ] RIGHT SQUARE BRACKET", body="# not a heading\n\n- not a list\n\n[not](a-link)")
    append_dispatch(entry, moment)
    text = Path("dispatches/2026/September.md").read_text(encoding="utf-8")
    assert "### ✨ U+005D \\] RIGHT SQUARE BRACKET" in text
    assert "\n\\# not a heading\n" in text and "\n\\- not a list\n" in text and "\\[not](a-link)" in text


def test_tip_example_cannot_close_its_own_fence(repo):
    region = render_modules_region({
        "tip": {"command": "x", "description": "d", "example": "echo ``` done", "url": "https://tldr.example/x"},
    })
    assert "> ````bash\n> echo ``` done\n> ````" in region
    assert not any(line.endswith("  ") for line in region.splitlines() if line.startswith(">"))


def test_month_badge_links_to_the_archive_before_the_first_entry(repo, moment):
    assert "(dispatches/)" in render_dispatches_region([], moment, 0)
    assert "(dispatches/2026/September.md)" in render_dispatches_region([], moment, 3)


def test_month_index_is_regenerated_between_markers(repo, moment):
    from datetime import datetime, timezone

    from render import update_month_index

    Path("dispatches").mkdir(exist_ok=True)
    Path("dispatches/README.md").write_text("intro\n\n<!-- MONTHS:BEGIN -->\n_Nothing sent yet._\n<!-- MONTHS:END -->\n\nouttro\n", encoding="utf-8")
    assert update_month_index() is False  # nothing to list yet, and the placeholder already says so
    append_dispatch(make_entry(identifier="1"), moment)
    append_dispatch(make_entry(identifier="2"), moment)
    append_dispatch(make_entry(identifier="3"), datetime(2026, 8, 2, 12, tzinfo=timezone.utc))
    text = Path("dispatches/README.md").read_text(encoding="utf-8")
    assert text.startswith("intro\n\n<!-- MONTHS:BEGIN -->\n| Month | Dispatches |\n| :--- | ---: |\n| [September 2026](2026/September.md) | 2 |\n| [August 2026](2026/August.md) | 1 |\n<!-- MONTHS:END -->")
    assert text.endswith("\n\nouttro\n")
