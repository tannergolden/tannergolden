#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The entry point the workflow runs. One run handles whatever is due this hour.

    python3 src/dispatches.py --mode tick      # the hourly run (default)
    python3 src/dispatches.py --mode dispatch  # send one dispatch now, whatever the schedule says
    python3 src/dispatches.py --mode refresh   # refresh the page now, on demand
    python3 src/dispatches.py --mode probe     # try every source and module, write nothing
    python3 src/dispatches.py --mode render    # re-render the page from state, offline
    python3 src/dispatches.py --mode check     # verify the page's regions, write nothing

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
import re
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
    DISPATCH_DIR,
    HORIZON_SECONDS,
    README,
    STATE_DIR,
)
from state import Ledger, Schedule, now
from text import clean, fit_subject

BADGE_DATA = ".github/badges.yml"

PROFILE_FILE = "profile.json"
COMMIT_PATHS = [README, DISPATCH_DIR, STATE_DIR, ASSETS_DIR, ".github/badges.yml"]


# --- git ------------------------------------------------------------------------

def git(*args: str, env: dict | None = None, check: bool = True) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=False, env=env)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr.strip()}")
    return result.stdout


def commit(message: str, paths: list | None = None) -> bool:
    """Stage the machine-owned paths and commit them with the message, from a file."""
    existing = [p for p in (paths or COMMIT_PATHS) if Path(p).exists()]
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
    if os.environ.get("DISPATCH_NO_PUSH") == "1":
        print(f"push skipped by DISPATCH_NO_PUSH (branch {branch})")
        report_unpushed(branch)
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


def report_unpushed(branch: str) -> None:
    """Write the commits a rehearsal made, but did not push, to the run summary.

    A dispatch on a branch other than the default one does everything except
    push, so the maintainer reads the result here rather than merging state
    files that the hourly runs on the default branch have moved on from.
    """
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    log = git("log", "--stat", "--format=full", f"origin/{branch}..HEAD", check=False)
    with open(summary, "a", encoding="utf-8") as handle:
        handle.write("### \U0001F4D3 Rehearsal: committed locally, not pushed\n\n")
        handle.write("```text\n" + (log.strip() or "nothing to report") + "\n```\n")


# --- badges -----------------------------------------------------------------------

def badge_status() -> str:
    """What the dispatch badge currently says, read back from the data file."""
    try:
        text = Path(BADGE_DATA).read_text(encoding="utf-8")
    except OSError:
        return ""
    block = re.search(r"- name: dispatches\n((?:[ \t]+\S.*\n){1,8})", text)
    if not block:
        return ""
    message = re.search(r"^\s+message:\s*['\"]?([^'\"\n]+?)['\"]?\s*$", block.group(1), flags=re.MULTILINE)
    return message.group(1).strip() if message else ""


BADGE_PATHS = [README, ".github/badges.yml", "assets/badges"]


def discard_partial_work() -> None:
    """Throw away whatever the failed run wrote, so none of it can be committed.

    A run that dies halfway has appended to the archive, touched the ledger
    and half-rendered the page. The failure commit must carry none of that,
    only the badge, so the tracked files go back to HEAD and anything new
    under the machine-owned paths is removed.
    """
    git("restore", "--source=HEAD", "--staged", "--worktree", "--", *COMMIT_PATHS, check=False)
    git("clean", "-fdq", "--", DISPATCH_DIR, STATE_DIR, ASSETS_DIR, check=False)


def mark_failed(exc: BaseException) -> None:
    """Turn the dispatch badge red and commit that, so the page tells the truth.

    A badge that cannot go red is decoration. This one goes red the moment
    a run fails, in a commit of its own that carries nothing fetched, and
    the next run that succeeds turns it back.
    """
    discard_partial_work()
    render_page(now(), with_modules=False, status=("Failing", "red"))
    if commit(render.failure_commit_message(f"{type(exc).__name__}: {exc}", now()), paths=BADGE_PATHS):
        push()


def mark_passing() -> None:
    """After a run that did no work, clear a red badge left by an earlier failure."""
    status = badge_status()
    if not status or status == "Passing":
        return
    render_page(now(), with_modules=False)
    if commit(render.recovery_commit_message(), paths=BADGE_PATHS):
        push()


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
            "--set", f"dispatches={status}:{color}",
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


def render_page(when: datetime, *, with_modules: bool = True, status: tuple = ("Passing", "green")) -> None:
    recent = render.load_recent()
    month_count = render.dispatches_this_month(when)
    # Badges first: the page embeds each one with a tag of its bytes.
    render_badges(month_count, *status)
    profile = load_profile()
    regions = {
        "DISPATCHES": render.render_dispatches_region(recent, when, month_count),
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
    render.update_month_index()


def write_dispatch(ledger: Ledger, when: datetime) -> str | None:
    """Write one dispatch to the archive, the index, the ledger and the page.

    Returns the commit message for it, or None when every source came back
    empty. Nothing is committed here: the caller draws the next moment first,
    so the schedule lands in the same commit as the dispatch it follows and
    one random moment is exactly one commit.
    """
    today = render.local(when).date()
    entry = sources.pick_dispatch(ledger, today)
    if entry is None:
        print("::warning::every source came back empty; skipping this dispatch until the next run.")
        return None

    path = render.append_dispatch(entry, when)
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


def probe() -> int:
    """Try every source and every module once, print what each would have written, change nothing.

    A throwaway ledger, no files, no commits. The one run that answers "do
    the adapters still work" without waiting for a random moment to find
    out, and the first thing to dispatch after a change to sources.py.
    """
    rows = []
    with tempfile.TemporaryDirectory() as scratch:
        ledger = Ledger(f"{scratch}/ledger.json")
        today = render.local(now()).date()
        for kind, fetcher in sources.FETCHERS.items():
            try:
                entry = fetcher(ledger, today)
            except Exception as exc:
                rows.append((kind, "error", clean(repr(exc))[:160]))
                continue
            if entry is None:
                rows.append((kind, "empty", "nothing available today"))
            else:
                rows.append((kind, "ok", fit_subject(entry.commit_type, entry.scope, entry.emoji, entry.subject)))

        profile = load_profile()
        try:
            tip = modules.terminal_tip(ledger)
        except Exception as exc:
            rows.append(("tip", "error", clean(repr(exc))[:160]))
        else:
            rows.append(("tip", "ok", clean(str(tip["command"]))[:120]) if tip else ("tip", "empty", "nothing new"))

        login = os.environ.get("GITHUB_REPOSITORY_OWNER") or profile.get("login") or "tannergolden"
        try:
            stats = cards.github_stats(login, os.environ.get("GITHUB_TOKEN"))
        except Exception as exc:
            rows.append(("stats", "error", clean(repr(exc))[:160]))
        else:
            if stats:
                rows.append(("stats", "ok", f"{stats['public_repos']} public repositories, {len(stats['languages'])} languages, commits {stats['commits']}"))
            else:
                rows.append(("stats", "empty", "the API returned nothing"))

    width = max(len(r[0]) for r in rows)
    lines = [f"{kind.ljust(width)}  {status:5}  {detail}" for kind, status, detail in rows]
    print("\n".join(lines))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("### \U0001F50D Probe: every source and module, nothing written\n\n")
            handle.write("| Source | Result | Would have written |\n| :--- | :--- | :--- |\n")
            for kind, status, detail in rows:
                mark = {"ok": "\u2705", "empty": "\u26aa", "error": "\u274c"}[status]
                handle.write(f"| {kind} | {mark} {status} | {render.md_inline(detail)} |\n")
    return 1 if any(status == "error" for _, status, _ in rows) else 0


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
            message = write_dispatch(ledger, now())
            if message and commit(message):
                push()
        moment = now()
        message = refresh_page(ledger, moment)
        schedule.reschedule_dispatch(after=moment)
        schedule.reschedule_refresh(after=moment)
        if commit(message):
            push()
        return 0

    while True:
        next_dispatch = schedule.next_dispatch
        next_refresh = schedule.next_refresh
        due = min(next_dispatch, next_refresh)
        if due > deadline:
            print(f"nothing due before {deadline.isoformat(timespec='seconds')}; next entry {next_dispatch.isoformat(timespec='seconds')}")
            mark_passing()
            return 0

        sleep_until(due)
        moment = now()
        if next_dispatch <= next_refresh:
            message = write_dispatch(ledger, moment)
            if message is None:
                # Leave the schedule alone: the dispatch is still due, and the
                # next run tries again. Stop here so this run cannot spin.
                return 0
            schedule.reschedule_dispatch(after=moment)
        else:
            message = refresh_page(ledger, moment)
            schedule.reschedule_refresh(after=moment)
        if commit(message):
            push()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mode", choices=["tick", "dispatch", "refresh", "render", "check", "probe"], default="tick")
    args = parser.parse_args()

    if args.mode == "probe":
        return probe()

    if args.mode == "check":
        document = Path(README).read_text(encoding="utf-8")
        for name in ("TYPING", "DISPATCHES", "MODULES", "CARDS", "UPDATED"):
            render.read_region(document, name)
        print("README.md: all five regions intact")
        return 0

    if args.mode == "render":
        render_page(now())
        print("README.md re-rendered from state")
        return 0

    try:
        return run_writing_mode(args.mode)
    except Exception as exc:
        print(f"::error::{type(exc).__name__}: {exc}")
        try:
            mark_failed(exc)
        except Exception as inner:
            print(f"::warning::could not mark the failure on the page: {inner!r}")
        raise


def run_writing_mode(mode: str) -> int:
    if mode == "refresh":
        # A forced refresh moves the next one the same way a forced dispatch
        # does, so the tick after it does not repeat the work an hour later.
        schedule = Schedule()
        moment = now()
        message = refresh_page(Ledger(), moment)
        schedule.reschedule_refresh(after=moment)
        if commit(message):
            push()
        return 0

    if mode == "dispatch":
        # One dispatch, now. The next moment is still drawn from the
        # distribution, so a forced dispatch moves the schedule the same way
        # a random one does rather than leaving a stale due time behind it.
        # The refresh is left alone on purpose. On a fresh deployment it has
        # no moment yet, which reads as due, so the next tick refreshes the
        # page within the hour rather than after a full draw.
        schedule = Schedule()
        moment = now()
        message = write_dispatch(Ledger(), moment)
        if message is None:
            return 1
        schedule.reschedule_dispatch(after=moment)
        if commit(message):
            push()
        return 0

    return tick()


if __name__ == "__main__":
    sys.exit(main())
