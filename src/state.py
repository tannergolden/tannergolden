# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The two files that make the process resumable, and the draw that paces it.

`state/schedule.json` holds the moment the next entry is due. `state/ledger.json`
holds the identifier of every item ever used. Both are committed alongside the
entry they describe, so the repository is its own database and a run starts by
reading what the previous run decided rather than by guessing.

WHY A DRAW AND NOT A PERIOD. A cron fires on a lattice. Waiting a fixed four
hours after each entry is also a lattice, just an offset one. The only way to
get moments that carry no schedule is to draw each wait from an exponential
distribution, which is the waiting time of a Poisson process: memoryless, so
knowing when the last entry landed tells you nothing about the next.

The draw comes from the operating system's entropy source. A seeded generator
would make the sequence reproducible, which is the opposite of the property
being bought here.
"""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import LEDGER_FILE, MEAN_INTERVAL_HOURS, MEAN_REFRESH_HOURS, SCHEDULE_FILE

# random.SystemRandom reads the OS entropy source (getrandom(2) on Linux), the
# same source `secrets` uses. `secrets` has no exponential draw of its own, so
# this is the stdlib's only way to get one that is not seeded.
_RNG = random.SystemRandom()


def now() -> datetime:
    return datetime.now(timezone.utc)


def draw_wait(mean_hours: float) -> timedelta:
    """Draw one exponentially distributed wait with the given mean.

    Bounded below at one second so two entries cannot share a timestamp, and
    above at eight means so a single unlucky draw cannot silence the page for
    a month. Both bounds are far enough into the tail to leave the shape of
    the distribution intact: at a 12 hour mean, the ceiling is four days and
    it is reached roughly once in three thousand draws.
    """
    mean_seconds = mean_hours * 3600.0
    seconds = _RNG.expovariate(1.0 / mean_seconds)
    return timedelta(seconds=min(max(seconds, 1.0), mean_seconds * 8))


def _read(path: str, fallback: dict) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return dict(fallback)
    return loaded if isinstance(loaded, dict) else dict(fallback)


def _write(path: str, payload: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
    os.replace(tmp, path)


class Schedule:
    """When the next entry and the next page refresh are due."""

    def __init__(self, path: str = SCHEDULE_FILE) -> None:
        self.path = path
        self._data = _read(path, {})

    def _get(self, key: str) -> datetime:
        raw = self._data.get(key)
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                pass
        # No state yet, or state written by something that did not understand
        # the format. Due immediately: a first run should populate the page
        # rather than wait half a day to prove it works.
        return now() - timedelta(seconds=1)

    def _set(self, key: str, when: datetime) -> None:
        self._data[key] = when.astimezone(timezone.utc).isoformat()
        _write(self.path, self._data)

    @property
    def is_fresh(self) -> bool:
        """True before the first run ever wrote a schedule."""
        return not any(key in self._data for key in ("next_dispatch", "next_refresh"))

    @property
    def next_dispatch(self) -> datetime:
        return self._get("next_dispatch")

    @property
    def next_refresh(self) -> datetime:
        return self._get("next_refresh")

    def reschedule_dispatch(self, *, after: datetime) -> datetime:
        when = after + draw_wait(MEAN_INTERVAL_HOURS)
        self._set("next_dispatch", when)
        return when

    def reschedule_refresh(self, *, after: datetime) -> datetime:
        when = after + draw_wait(MEAN_REFRESH_HOURS)
        self._set("next_refresh", when)
        return when


class Ledger:
    """Every identifier ever used, so nothing appears twice.

    Keyed by kind, and the identifier is whatever uniquely names the item at
    its source: an RFC number, a Unicode code point, an OEIS A-number, a
    Rosetta Code task and language pair. Storing the source's
    own identifier rather than a hash of the rendered text means an item stays
    recognised after its wiki page is reworded.
    """

    def __init__(self, path: str = LEDGER_FILE) -> None:
        self.path = path
        data = _read(path, {})
        self._used: dict[str, set[str]] = {
            kind: set(map(str, ids)) for kind, ids in data.items() if isinstance(ids, list)
        }
        self._retired: set[str] = set(map(str, data.get("_retired", []) or []))
        self._used.pop("_retired", None)

    def seen(self, kind: str, identifier: str) -> bool:
        return str(identifier) in self._used.get(kind, set())

    def remember(self, kind: str, identifier: str) -> None:
        self._used.setdefault(kind, set()).add(str(identifier))

    def retire(self, kind: str) -> None:
        """Mark a kind as having run out, so the picker stops offering it.

        Two kinds draw on finite hand-curated lists rather than on a growing
        corpus. When one is exhausted it retires rather than repeating itself,
        and the remaining weight redistributes across what is left.
        """
        self._retired.add(kind)

    @property
    def retired(self) -> set[str]:
        return set(self._retired)

    def count(self, kind: str) -> int:
        return len(self._used.get(kind, set()))

    def used(self, kind: str) -> set[str]:
        return set(self._used.get(kind, set()))

    def save(self) -> None:
        payload: dict = {kind: sorted(ids) for kind, ids in self._used.items() if ids}
        if self._retired:
            payload["_retired"] = sorted(self._retired)
        _write(self.path, payload)
