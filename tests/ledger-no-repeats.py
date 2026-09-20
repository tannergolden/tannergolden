# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""No identifier is ever used twice, and the draw weights are what the design says."""

from __future__ import annotations

from sources import COMMON, RARE, RARE_SHARE, draw_order, weights
from state import Ledger


def test_ledger_round_trips(repo):
    ledger = Ledger("state/ledger.json")
    assert not ledger.seen("rfc", "327")
    ledger.remember("rfc", "327")
    ledger.remember("rosetta", "FizzBuzz|COBOL")
    ledger.retire("bug")
    ledger.save()

    again = Ledger("state/ledger.json")
    assert again.seen("rfc", "327") and again.seen("rfc", 327)
    assert again.used("rosetta") == {"FizzBuzz|COBOL"}
    assert again.retired == {"bug"}
    assert again.count("rfc") == 1


def test_weights_give_the_rare_pair_one_draw_in_twenty():
    w = weights(set())
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert abs(sum(w[k] for k in RARE) - RARE_SHARE) < 1e-9
    common = {w[k] for k in COMMON}
    assert len(common) == 1  # equal weight


def test_retired_kinds_leave_the_draw_and_the_rest_renormalises():
    w = weights({"bug", "falsehood"})
    assert set(w) == set(COMMON)
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert all(abs(v - 1 / len(COMMON)) < 1e-9 for v in w.values())


def test_draw_order_covers_every_live_kind_exactly_once():
    order = draw_order({"falsehood"})
    assert sorted(order) == sorted(set(COMMON) | {"bug"})
