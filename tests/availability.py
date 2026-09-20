# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The one line on the page a person sets, and the commit that sets it.

Everything else here is written by a source. This is written by whoever runs
the workflow, which makes it the only place where saying nothing is safer
than guessing: a profile that silently claims to be looking for work, or not
to be, is worse than one that carries no badge at all.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

import dispatches
import render


def test_the_three_states_are_the_three_the_dropdown_offers():
    """The workflow maps its labels onto these keys and nothing else."""
    assert set(render.AVAILABILITY) == {"role", "consult", "none"}
    workflow = Path(__file__).resolve().parent.parent / ".github/workflows/availability.yml"
    text = workflow.read_text(encoding="utf-8")
    for label in ("Open to role", "Open to consult", "Not Available"):
        assert f"'\U0001F7E2 {label}'" in text or f"'\U0001F7E1 {label}'" in text \
            or f"'\U0001F534 {label}'" in text, label
    # Every message the states carry is a label the dropdown can send.
    for message, _ in render.AVAILABILITY.values():
        assert message in text, message


def test_each_state_carries_its_own_health_colour():
    assert render.AVAILABILITY["role"][1] == "green"
    assert render.AVAILABILITY["consult"][1] == "yellow"
    assert render.AVAILABILITY["none"][1] == "red"
    for state in render.AVAILABILITY:
        message, colour = render.AVAILABILITY[state]
        assert render.availability_badge_set(state) == f"availability={message}:{colour}"


def test_an_unset_status_renders_nothing_rather_than_a_guess(repo):
    assert render.load_availability() == ""
    assert render.render_availability_region("") == ""
    assert render.render_availability_region("nonsense") == ""


def test_the_region_is_a_badge_and_not_a_line_of_text(repo):
    Path("assets/badges/dynamic").mkdir(parents=True)
    Path(render.AVAILABILITY_BADGE).write_text("<svg>role</svg>", encoding="utf-8")
    region = render.render_availability_region("role")
    assert region.startswith("[![Availability: Open to role](")
    assert render.AVAILABILITY_BADGE in region
    # Cache busting: GitHub proxies images by URL, so a rewritten badge needs
    # a new one or a stale status stays on the page for hours.
    assert re.search(r"availability\.svg\?v=[0-9a-f]{8}\)", region)


def test_a_changed_badge_gets_a_new_url(repo):
    Path("assets/badges/dynamic").mkdir(parents=True)
    Path(render.AVAILABILITY_BADGE).write_text("<svg>role</svg>", encoding="utf-8")
    before = render.render_availability_region("role")
    Path(render.AVAILABILITY_BADGE).write_text("<svg>not available</svg>", encoding="utf-8")
    assert render.render_availability_region("none") != before


def test_the_state_round_trips_through_its_own_file(repo):
    render.save_availability("consult")
    assert json.loads(Path("state/availability.json").read_text(encoding="utf-8")) == {"state": "consult"}
    assert render.load_availability() == "consult"

    # A file somebody hand-edited into nonsense reads as unset, not as a crash.
    Path("state/availability.json").write_text('{"state": "looking"}', encoding="utf-8")
    assert render.load_availability() == ""
    Path("state/availability.json").write_text("not json", encoding="utf-8")
    assert render.load_availability() == ""

    with pytest.raises(ValueError):
        render.save_availability("looking")


def test_the_commit_message_holds_to_the_house_standard(repo):
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("gate", Path(__file__).resolve().parent / "commit-message.py")
    gate = module_from_spec(spec)
    sys.modules["gate"] = gate
    spec.loader.exec_module(gate)

    for state in render.AVAILABILITY:
        for _ in range(30):  # the verb and the emoji are drawn
            message = render.availability_commit_message(state)
            assert gate.problems_for(message) == [], message
            header, _, rest = message.partition("\n\n")
            assert len(header) <= 72, header
            assert rest.strip(), "the body is required"
            assert render.AVAILABILITY[state][0].lower() in message


def test_a_no_op_run_stages_nothing_and_pushes_nothing(repo, monkeypatch):
    """Whether anything changed is git's question, asked by staging it.

    An earlier version answered it from the state file and returned before
    rendering, which meant a badge left stale by a failed run could never be
    redrawn by picking the same status again.
    """
    pushes = []
    monkeypatch.setattr(dispatches, "render_page", lambda *a, **k: None)
    monkeypatch.setattr(dispatches, "push", lambda: pushes.append(1))
    staged = iter([True, False])  # what git would say: something, then nothing
    monkeypatch.setattr(dispatches, "commit", lambda *a, **k: next(staged))

    assert dispatches.set_availability("role") == 0
    assert pushes == [1]
    assert dispatches.set_availability("role") == 0
    assert pushes == [1], "a run with nothing staged pushed anyway"


def test_the_badge_is_in_the_paths_the_run_can_commit(repo, monkeypatch):
    """The badge lives under assets; a run that redraws it must stage it."""
    seen = {}
    monkeypatch.setattr(dispatches, "render_page", lambda *a, **k: None)
    monkeypatch.setattr(dispatches, "push", lambda: None)
    monkeypatch.setattr(dispatches, "commit", lambda msg, paths=None: seen.update(paths=paths) or False)
    dispatches.set_availability("role")
    assert "assets" in seen["paths"], seen["paths"]
    assert Path(render.AVAILABILITY_BADGE).parts[0] in seen["paths"]


def test_an_unknown_status_changes_nothing(repo, monkeypatch):
    monkeypatch.setattr(dispatches, "commit", lambda *a, **k: pytest.fail("committed anyway"))
    assert dispatches.set_availability("looking") == 1
    assert dispatches.set_availability(None) == 1
    assert not Path("state/availability.json").exists()
