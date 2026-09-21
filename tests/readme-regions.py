# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Only the inside of a marked region is ever written; everything else is byte-identical."""

from __future__ import annotations

from pathlib import Path

import pytest

from render import read_region, replace_region, update_readme


def test_replace_touches_only_the_region(repo):
    before = Path("README.md").read_text(encoding="utf-8")
    after = replace_region(before, "DISPATCHES", "new dispatches")
    assert read_region(after, "DISPATCHES") == "new dispatches"
    assert read_region(after, "MODULES") == "old modules"
    head, _, _ = before.partition("<!-- DISPATCHES:BEGIN -->")
    assert after.startswith(head)
    _, _, tail = before.partition("<!-- DISPATCHES:END -->")
    assert after.endswith(tail)


def test_missing_marker_refuses_to_write(repo):
    with pytest.raises(ValueError):
        replace_region("no markers here", "DISPATCHES", "x")


def test_update_readme_reports_change(repo):
    assert update_readme({"UPDATED": "Last updated now."}) is True
    assert update_readme({"UPDATED": "Last updated now."}) is False
    text = Path("README.md").read_text(encoding="utf-8")
    assert "prose before" in text and "prose after" in text


# --- the masthead document -------------------------------------------------------

SPELLED = {4: "four", 8: "eight", 12: "twelve", 34: "thirty-four"}


def test_the_masthead_document_still_tells_the_truth(repo):
    """Every number in Masthead.md, checked against the code that produces it.

    These figures have moved four times in one sitting. A document nobody
    verifies is a document that is wrong within a week, and this one exists
    to be quoted, so the quotable parts are pinned here.
    """
    import re
    from pathlib import Path

    import cards
    import masthead

    doc = Path(__file__).resolve().parent.parent.joinpath("Masthead.md").read_text("utf-8")
    cell = cards.MASTHEAD_FONT_SIZE * cards.CELL_RATIO

    def image(cells):
        return int(cards.MASTHEAD_TEXT_X + (cards.PROMPT_CELLS + cells) * cell) \
            + cards.MASTHEAD_TEXT_X

    expected = {
        "lines": f"**{masthead.TOTAL_LINES:,}** exactly",
        "drawable": f"| Of those, narrow enough to show | {masthead.drawable()} |",
        "frames": f"| Frames | {len(masthead.FRAMES)}, of which "
                  f"{len(masthead.plate_frames())} fit the plate |",
        "mastheads": f"**{masthead.mastheads():,}** distinct mastheads",
        "commits": f"| Distinct commit messages | {masthead.commit_messages():,} |",
        "plate": f"draws only from lines that fit **{masthead.PLATE_CELLS} cells**",
        # Prose spells the small numbers, so the check has to as well or it
        # pins nothing that a reader would ever see.
        "floor": f"keep at least **{SPELLED[masthead.PLATE_MIN_LINES]}**",
        "undrawable": f"This costs {masthead.combinations() - masthead.drawable()} lines",
        "breakpoint": f"(max-width: {cards.masthead_breakpoint()}px)",
        "plate image": f"| **{masthead.PLATE_CELLS} cells (the plate)** | **{image(34)}px**",
        "memory": f"last {SPELLED[masthead.MEMORY_DRAWS]} draws",
        "typing": f"{round(1 / cards.TYPE_CADENCE)} cells a second",
        "still rows": f"first {SPELLED[cards.STILL_ROWS]} lines",
    }
    for what, claim in expected.items():
        assert claim in doc, f"Masthead.md no longer says the right thing about {what}: {claim}"

    # And the shape of the document itself.
    assert doc.startswith("<!--\ntitle: '⌨️ THE MASTHEAD'")
    assert doc.count("tags: [") == 1
    assert len(re.search(r"tags: \[([^\]]+)\]", doc).group(1).split(",")) == 4
    assert "---\n" not in doc.split("-->")[0], "frontmatter must not be fenced"
    assert '<a name="top"></a>' in doc and "[↑ Back to Top](#top)" in doc
    assert not re.search("[\u2013-\u2015]", doc), "a dash the house bans"
