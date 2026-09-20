# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The draw has the right shape, and the schedule file round-trips with its zone."""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from state import Schedule, draw_wait, now


def test_draw_is_bounded_and_has_the_right_mean():
    waits = [draw_wait(12).total_seconds() for _ in range(3000)]
    assert min(waits) >= 1.0
    assert max(waits) <= 12 * 3600 * 8
    mean = sum(waits) / len(waits)
    assert 0.8 * 12 * 3600 < mean < 1.2 * 12 * 3600, mean


def test_draws_are_not_a_lattice():
    waits = {round(draw_wait(12).total_seconds()) for _ in range(200)}
    assert len(waits) > 190


def test_fresh_schedule_is_due_at_once(repo):
    schedule = Schedule("state/schedule.json")
    assert schedule.is_fresh
    assert schedule.next_entry < now()
    assert schedule.next_refresh < now()


def test_reschedule_persists_an_aware_utc_timestamp(repo):
    schedule = Schedule("state/schedule.json")
    when = schedule.reschedule_entry(after=now())
    assert when > now()
    stored = json.loads(Path("state/schedule.json").read_text(encoding="utf-8"))
    assert stored["next_entry"].endswith("+00:00")
    again = Schedule("state/schedule.json")
    assert not again.is_fresh
    assert abs((again.next_entry - when).total_seconds()) < 1
    assert again.next_entry - now() < timedelta(hours=12 * 8 + 1)
