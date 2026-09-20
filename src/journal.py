#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The entry point the workflow runs. One run handles whatever is due this hour.

    python3 src/journal.py --mode tick      # the hourly run (default)
    python3 src/journal.py --mode refresh   # refresh the page now, on demand
    python3 src/journal.py --mode render    # re-render the page from state, offline
    python3 src/journal.py --mode check     # verify the page's regions, write nothing

HOW A TICK WORKS. The schedule file holds two moments: when the next entry is
due and when the next page refresh is due. The run reads both, and if either
falls inside the coming hour it sleeps until that exact second, does the work,
draws the next moment from the exponential distribution, and looks again. A
moment already in the past, because a cron was skipped or the runner was
late, is handled immediately: the entry lands late rather than never. When
nothing is due this hour the run ends in seconds.

Every commit is authored by the account owner and committed by the Actions
identity, then pushed after a rebase, so a run never overwrites a change a
person made in the meantime.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import cards
import modules
import render
import sources
from config import (
    ASSETS_DIR,
    BOOTSTRAP_ENTRIES,
    HORIZON_SECONDS,
    JOURNAL_DIR,
    README,
    STATE_DIR,
)
from state import Ledger, Schedule, now

PROFILE_FILE = "profile.json"
COMMIT_PATHS = [README, JOURNAL_DIR, STATE_DIR, ASSETS_DIR, ".github/badges.yml"]


# --- git ------------------------------------------------------------------------

def git(*args: str, env: dict | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False, env=env)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def commit(message: str) -> bool:
    """Stage the machine-owned paths and commit them with the message, from a file."""
    existing = [p for p in COMMIT_PATHS if Path(p).exists()]
    git("add", "--", *existing)
    if not git("diff", "--cached", "--name-only").strip():
        print("nothing to commit")
        return False
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as handle:
        handle.write(message)
        path = handle.name
    try:
        git("commit", "--quiet", "-F", path, env=render.git_env_for_commit())
    finally:
        os.unlink(path)
    print(f"committed: {message.splitlines()[0]}")
    return True


def push() -> None:
    """Rebase onto whatever landed meanwhile, then push. Retried, never forced."""
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    if os.environ.get("JOURNAL_NO_PUSH") == "1":
        print(f"push skipped by JOURNAL_NO_PUSH (branch {branch})")
        return
    delay = 2
    for attempt in range(1, 6):
        try:
            git("pull", "--rebase", "--autostash", "--quiet", "origin", branch)
            git("push", "--quiet", "origin", f"HEAD:{branch}")
            print(f"pushed to {branch}")
            return
        except RuntimeError as exc:
            print(f"::warning::push attempt {attempt} failed: {exc}")
            if attempt == 5:
                raise
            time.sleep(delay)
            delay *= 2


# --- badges -----------------------------------------------------------------------

def render_badges(month_count: int, status: str = "Passing", color: str = "green") -> None:
    """Re-render the committed badges through the emblems kit, when it is present.

    The workflow checks the kit out beside this repository; locally, point
    EMBLEMS_KIT at a clone. Without it the badges keep their last rendering,
    which is a stale number rather than a broken image.
    """
    kit = os.environ.get("EMBLEMS_KIT", ".emblems/src/badge-kit.py")
    if not Path(kit).exists():
        print(f"::warning::emblems kit not found at {kit}; badges left as they are.")
        return
    result = subprocess.run(
        [
            sys.executable, kit, "--root", ".", "--data", ".github/badges.yml", "--out", "assets/badges",
            "--set", f"journal={status}:{color}",
            "--set", f"month={render.month_badge_message(month_count)}:green",
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        print(f"::warning::badge rendering failed:\n{result.stderr.strip()}")


# --- the work -----------------------------------------------------------------------

def load_profile() -> dict:
    try:
        return json.loads(Path(PROFILE_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def render_page(when: datetime, *, with_modules: bool = True) -> None:
    recent = render.load_recent()
    month_count = render.entries_this_month(when)
    profile = load_profile()
    regions = {
        "JOURNAL": render.render_journal_region(recent, when, month_count),
        "UPDATED": render.render_updated_line(when),
        "TYPING": cards.picture("typing", " / ".join(profile.get("phrases") or ["engineering"])),
    }
    if with_modules:
        alts = cards.load_card_alts()
        regions["MODULES"] = render.render_modules_region(render.load_modules())
        regions["CARDS"] = (
            cards.picture("stats", alts.get("stats_alt", "GitHub statistics card"))
            + "\n"
            + cards.picture("languages", alts.get("languages_alt", "Top languages card"))
        )
    render.update_readme(regions)
    render_badges(month_count)


def write_entry(ledger: Ledger, when: datetime) -> str | None:
    """Write one entry to the journal, the index, the ledger and the page.

    Returns the commit message for it, or None when every source came back
    empty. Nothing is committed here: the caller draws the next moment first,
    so the schedule lands in the same commit as the entry it follows and one
    random moment is exactly one commit.
    """
    today = render.local(when).date()
    entry = sources.pick_entry(ledger, today)
    if entry is None:
        print("::warning::every source came back empty; skipping this entry until the next run.")
        return None

    path = render.append_journal(entry, when)
    render.record_recent(entry, when, path)
    ledger.remember(entry.kind, entry.identifier)
    ledger.save()
    render_page(when, with_modules=False)
    return render.commit_message(entry)


def refresh_page(ledger: Ledger, when: datetime) -> str:
    """Refresh the modules, the images and the page; return the commit message."""
    profile = load_profile()
    changed = []

    current = render.load_modules()
    hn = modules.show_hn(ledger)
    if hn:
        current["hn"] = hn
        changed.append("the Show HN post")
    issue = modules.good_first_issue(ledger, list(profile.get("issue_languages") or []))
    if issue:
        current["issue"] = issue
        changed.append("the good first issue")
    tip = modules.terminal_tip(ledger)
    if tip:
        current["tip"] = tip
        changed.append("the terminal tip")
    render.save_modules(current)
    ledger.save()

    cards.write_typing(profile)
    login = os.environ.get("GITHUB_REPOSITORY_OWNER") or profile.get("login") or "tannergolden"
    stats = cards.github_stats(login, os.environ.get("GITHUB_TOKEN"))
    if stats:
        cards.write_cards(stats)
        changed.append("the cards")

    render_page(when)
    return render.readme_commit_message(when, changed)


def sleep_until(moment: datetime) -> None:
    while True:
        remaining = (moment - now()).total_seconds()
        if remaining <= 0:
            return
        step = min(remaining, 300)
        print(f"sleeping {int(remaining)}s until {moment.isoformat(timespec='seconds')}")
        time.sleep(step)


def tick() -> int:
    schedule = Schedule()
    ledger = Ledger()
    started = now()
    deadline = started + timedelta(seconds=HORIZON_SECONDS)

    if schedule.is_fresh and BOOTSTRAP_ENTRIES > 0:
        # The very first run. Populate the page rather than leave it empty
        # for half a day, then draw the first moments and start the process.
        print(f"no schedule yet: bootstrapping {BOOTSTRAP_ENTRIES} entries and a refresh")
        for _ in range(BOOTSTRAP_ENTRIES):
            message = write_entry(ledger, now())
            if message and commit(message):
                push()
        moment = now()
        message = refresh_page(ledger, moment)
        schedule.reschedule_entry(after=moment)
        schedule.reschedule_refresh(after=moment)
        if commit(message):
            push()
        return 0

    while True:
        next_entry = schedule.next_entry
        next_refresh = schedule.next_refresh
        due = min(next_entry, next_refresh)
        if due > deadline:
            print(f"nothing due before {deadline.isoformat(timespec='seconds')}; next entry {next_entry.isoformat(timespec='seconds')}")
            return 0

        sleep_until(due)
        moment = now()
        if next_entry <= next_refresh:
            message = write_entry(ledger, moment)
            if message is None:
                # Leave the schedule alone: the entry is still due, and the
                # next run tries again. Stop here so this run cannot spin.
                return 0
            schedule.reschedule_entry(after=moment)
        else:
            message = refresh_page(ledger, moment)
            schedule.reschedule_refresh(after=moment)
        if commit(message):
            push()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["tick", "refresh", "render", "check"], default="tick")
    args = parser.parse_args()

    if args.mode == "check":
        document = Path(README).read_text(encoding="utf-8")
        for name in ("TYPING", "JOURNAL", "MODULES", "CARDS", "UPDATED"):
            render.read_region(document, name)
        print("README.md: all five regions intact")
        return 0

    if args.mode == "render":
        render_page(now())
        print("README.md re-rendered from state")
        return 0

    if args.mode == "refresh":
        if commit(refresh_page(Ledger(), now())):
            push()
        return 0

    return tick()


if __name__ == "__main__":
    sys.exit(main())
