#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The one clock for all four games on the profile: twice an hour, each game's Arbiter, in a single run.

  python3 .github/scripts/clock.py .github [--now 2026-10-12T17:00:00Z]

.github/workflows/clock.yml runs this twice an hour, off the hour, and no
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
from page import load, marks, now_utc, parse, set_out

LOGIN, ID = games.LOGIN, games.ID


def boards(root: Path, owner: str, owner_id: int, moment) -> dict:
    """Every game's board and the Hall of Fame of all four, from the state in the checkout."""
    states = halls.load(root)
    out = {key: [(key, games.board(games.rules(key), *states[key], owner, moment))] for key in games.GAMES}
    out["chess"] = [("chess", chess.board(*states["chess"], owner, moment))]
    out["hall"] = [("hall-of-fame", halls.element(states, owner, owner_id))]
    return {key: out[key] for key in (*halls.GAMES, "hall")}


NAMES = {"hall": "the Hall of Fame"}  # a region by the name a reader knows it by, where its key is not that name


def series(items: list[str]) -> str:
    """`a`, `a and b`, `a, b and c`."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def showing(settings: Path) -> set[str]:
    """The games whose region in the settings sets out a finished game's final board, its result on show."""
    lines = settings.read_text(encoding="utf-8").splitlines() if settings.exists() else []
    out = set()
    for key in halls.GAMES:
        found = marks(lines, key)
        if found and any(line.startswith("    result: ") for line in lines[found[0] + 1:found[1]]):
            out.add(key)
    return out


def message(commits: list[tuple[str, str]], drawn: list[str], fresh: frozenset[str] | set[str] = frozenset()) -> str:
    """The run's one commit: a game's own when it alone moved on, else one that names every game and keeps theirs.
    When no game moved and boards were set out again, it says why: for each game in `fresh`, a final board's two days
    are up and the fresh board has come; for the rest, the engine now sets them out differently."""
    if len(commits) == 1:
        return commits[0][1]
    if commits:
        return (f"chore(games): ⏰ run the clock for {series([key for key, _ in commits])}\n\n"
                + "\n\n".join(text for _, text in commits))
    if not drawn:
        return ""
    came = [key for key in drawn if key in fresh]
    rest = [NAMES.get(key, key) for key in drawn if key not in fresh]
    said = []
    if came:
        said.append(f"The clock set out {series(came)} again: " + (
            "a final board's two days are up, and the fresh board has come." if len(came) == 1
            else "their final boards' two days are up, and their fresh boards have come."))
    if rest:
        said.append(f"{'It also set out' if came else 'The clock set out'} {series(rest)} again, as the engine sets"
                    f" {'it' if len(rest) == 1 else 'them'} out now: no game moved.")
    return f"chore(games): 🖌️ set the boards out for the page\n\n{textwrap.fill(' '.join(said), 72)}"


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
        regions = boards(args.root, owner, int(owner_id), moment)
        finals = showing(args.settings)  # before the boards are set out over them
        drawn = set_out(args.settings, regions)
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    fresh = {key for key in drawn if key in finals and "result" not in regions[key][0][1]}
    run = env.get("RUN_URL", "")
    commit = message(commits, drawn, fresh)
    (out / "notices.txt").write_text("".join(f"{line}\n" for line in notices), encoding="utf-8")
    (out / "commit.txt").write_text(commit + (f"\n\nRun: {run}" if run and commit else "") + "\n", encoding="utf-8")
    if "GITHUB_OUTPUT" in env:
        with open(env["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
            handle.write(f"changed={'true' if changed or drawn else 'false'}\n")
            handle.write(f"notices={len(notices)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
