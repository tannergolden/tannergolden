#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The one clock for all four games on the profile: every hour on the hour, each game's Arbiter, in a single run.

  python3 .github/scripts/clock.py .github [--now 2026-10-12T17:00:00Z]

.github/workflows/clock.yml runs this at the top of every hour, and no
game's own workflow keeps a schedule of its own. For each game, in tier
order (Tic-Tac-Toe, Connect Four, Checkers, Chess), it does what that game's
clock does: the first game of Checkers starts, GitHub to open it as Black,
and those of Tic-Tac-Toe and Connect Four open; once a finished game's two
days are up, the next game's fresh board comes, in Tic-Tac-Toe and Connect
Four with the Arbiter's random opening on it, for a side drawn at random;
and when the side to move has gone a week without moving, the Arbiter plays
a random legal move for it. Every game whose state changed is saved, every
board and the Hall of Fame of all four are set out again between their
markers in .github/markdown.yaml, and one commit and one redraw cover them
all.

Each game's notice of the Arbiter's move goes in <out>/<game>.md, listed in
<out>/notices.txt a line each: the issue it goes on, or `logbook` for the
owner's logbook, then the file, for the workflow to post through the
Arbiter. It writes commit.txt there too, and sets `changed` (whether the page
is to be drawn again) and `notices` (how many there are) as step outputs.
Stdlib only, with every game's script beside it.
"""
from __future__ import annotations

import argparse
import os
import sys
import textwrap
from pathlib import Path

import chess
import games
import hall as halls
from page import load, now_utc, parse, set_out

LOGIN, ID = games.LOGIN, games.ID


def boards(root: Path, owner: str, owner_id: int, moment) -> dict:
    """Every game's board and the Hall of Fame of all four, from the state in the checkout."""
    states = halls.load(root)
    out = {key: [(key, games.board(games.rules(key), *states[key], owner, moment))] for key in games.GAMES}
    out["chess"] = [("chess", chess.board(*states["chess"], owner, moment))]
    out["hall"] = [("hall-of-fame", halls.element(states, owner, owner_id))]
    return {key: out[key] for key in (*halls.GAMES, "hall")}


def message(commits: list[tuple[str, str]], drawn: list[str]) -> str:
    """The run's one commit: a game's own when it alone moved on, else one that names every game and keeps theirs."""
    if len(commits) == 1:
        return commits[0][1]
    if commits:
        keys = [key for key, _ in commits]
        names = " and ".join(keys) if len(keys) < 3 else ", ".join(keys[:-1]) + " and " + keys[-1]
        return f"chore(games): ⏰ run the clock for {names}\n\n" + "\n\n".join(text for _, text in commits)
    if drawn:
        body = (f"The clock set out {', '.join(drawn)} again: a final board's two days are up, and the fresh board"
                " has come.")
        return f"chore(games): 🖌️ set the boards out for the page\n\n{textwrap.fill(body, 72)}"
    return ""


def main(argv: list[str] | None = None, env: dict | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("root", type=Path, nargs="?", default=Path(".github"),
                        help="the folder that holds every game's state (default: .github)")
    parser.add_argument("--out", type=Path, help="where the notices and commit.txt go (default: $RUNNER_TEMP)")
    parser.add_argument("--now", help="the time to run at, ISO 8601 (default: now)")
    parser.add_argument("--settings", type=Path, default=Path(".github/markdown.yaml"),
                        help="the page's settings, where the boards are set out (default: .github/markdown.yaml)")
    args = parser.parse_args(argv)
    env = dict(os.environ) if env is None else env
    owner, owner_id = env.get("OWNER", ""), env.get("OWNER_ID", "")
    if not LOGIN.fullmatch(owner) or not ID.fullmatch(owner_id):
        print("::error::OWNER and OWNER_ID name the house, and one is missing or malformed.")
        return 1
    moment = parse(args.now) if args.now else now_utc()
    out = args.out or Path(env.get("RUNNER_TEMP", "."))
    out.mkdir(parents=True, exist_ok=True)
    commits, notices, changed = [], [], False
    for key in halls.GAMES:
        folder = args.root / key
        game, hall = load(folder)
        if key == "chess":
            outcome = chess.tick(game, hall, owner, moment)
            if outcome.changed:
                chess.save(folder, outcome)
        else:
            outcome = games.tick(games.rules(key), game, hall, owner, moment)
            if outcome.changed:
                games.save(folder, outcome)
        if outcome.changed:
            changed = True
            commits.append((key, outcome.commit))
        if outcome.comment:
            (out / f"{key}.md").write_text(outcome.comment, encoding="utf-8")
            notices.append(f"{'logbook' if outcome.logbook else outcome.issue} {key}.md")
        print(f"{key}: {outcome.log}.")
    try:
        drawn = set_out(args.settings, boards(args.root, owner, int(owner_id), moment))
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    run = env.get("RUN_URL", "")
    commit = message(commits, drawn)
    (out / "notices.txt").write_text("".join(f"{line}\n" for line in notices), encoding="utf-8")
    (out / "commit.txt").write_text(commit + (f"\n\nRun: {run}" if run and commit else "") + "\n", encoding="utf-8")
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if changed or drawn else 'false'}\n")
            handle.write(f"notices={len(notices)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
