# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""No identifier is ever used twice, and every kind gets an equal turn."""

from __future__ import annotations

import sources
from sources import KINDS, draw_order
from state import Ledger


def test_ledger_round_trips(repo):
    ledger = Ledger("state/ledger.json")
    assert not ledger.seen("rfc", "327")
    ledger.remember("rfc", "327")
    ledger.remember("release", "golang/go@go1.25.0")
    ledger.save()

    again = Ledger("state/ledger.json")
    assert again.seen("rfc", "327") and again.seen("rfc", 327)
    assert again.used("release") == {"golang/go@go1.25.0"}
    assert again.count("rfc") == 1


def test_a_retired_key_from_the_old_format_is_not_read_back_as_a_kind(repo):
    """An earlier design could retire a kind. A state file may still say so."""
    (repo / "state").mkdir(exist_ok=True)
    (repo / "state/ledger.json").write_text('{"_retired": ["bug"], "rfc": ["1"]}', encoding="utf-8")
    ledger = Ledger("state/ledger.json")
    assert ledger.seen("rfc", "1")
    assert ledger.count("_retired") == 0
    ledger.save()
    assert "_retired" not in (repo / "state/ledger.json").read_text(encoding="utf-8")


def test_draw_order_offers_every_kind_exactly_once():
    for _ in range(50):
        assert sorted(draw_order()) == sorted(KINDS)


def test_the_order_actually_varies():
    """A fixed order would mean one source always answers first and the rest never do."""
    assert len({tuple(draw_order()) for _ in range(200)}) > 1


def test_every_kind_is_wired_to_a_fetcher():
    assert set(sources.FETCHERS) == set(KINDS)
