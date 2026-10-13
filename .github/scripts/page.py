# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""What the profile's four games share with the page they are drawn on: its time, its days and its settings.

  from page import DISPLAY, WEEK, day, until, handle, set_out

The page tells time in EST, as its settings say, and writes a day as `18 Oct`
and a deadline as `18 Oct, 12:31 EST`. A side has a week to move before the
Arbiter moves for it (`WEEK`), and a finished game's final board stays up for
two days before the next game's fresh board comes (`DISPLAY`).

Every game sets its board out for the page between its own marker lines under
`elements:` in .github/markdown.yaml, and the Hall of Fame of all four games
between its own: `# tictac:start` and `# tictac:end`, then pentago, checkers,
chess and hall. `set_out` writes the regions it is given, each only
when it changed, and adds a region whose markers are missing at the end of
`elements:`; nothing else in the file is touched. Stdlib only.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

WEEK = dt.timedelta(days=7)  # how long a side has to move before the Arbiter moves for it
DISPLAY = dt.timedelta(days=2)  # how long a finished game's final board stays up
EST = dt.timezone(dt.timedelta(hours=-5), "EST")  # the page tells time in EST, as its settings say
NOTE = 400  # the most a note under a board may run to, as the kit takes a line of the README
REGIONS = ("tictac", "pentago", "checkers", "chess", "hall")  # the settings' regions, in the page's order
HOUSE, GITHUB = "house", "github"  # the two sides of every game: the owner of the profile, and everyone else


def other(side: str) -> str:
    """The other side of a game."""
    return GITHUB if side == HOUSE else HOUSE


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def stamp(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def until(moment: dt.datetime) -> str:
    """A deadline as the page tells time: `18 Oct, 12:31 EST`."""
    local = moment.astimezone(EST)
    return f"{local.day} {local:%b}, {local:%H:%M} EST"


def day(moment: dt.datetime) -> str:
    """A day as the page's sheets letter it, in the page's time: `18 Oct`."""
    local = moment.astimezone(EST)
    return f"{local.day} {local:%b}"


def date(moment: dt.datetime) -> str:
    """A day with its year, in the page's time: `18 Oct 2026`."""
    local = moment.astimezone(EST)
    return f"{local.day} {local:%b} {local.year}"


def profile(owner: str) -> str:
    return f"https://github.com/{owner}"


def handle(login: str) -> str:
    """A player named without a ping: the @handle as a link to their profile, which GitHub never turns into a
    mention. A turned-away move pings nobody, so nobody can ping anyone by opening issues."""
    return f"[@{login}]({profile(login)})"


def sentences(parts: list[tuple[str, bool]], most: int = NOTE) -> str:
    """A note's sentences in order: each one that must be said, and each one that may be said when it leaves room for
    every one after it that must."""
    out: list[str] = []
    for index, (text, must) in enumerate(parts):
        later = sum(len(after) + 1 for after, needed in parts[index + 1:] if after and needed)
        if text and (must or len(" ".join([*out, text])) + later <= most):
            out.append(text)
    return " ".join(out)


def flow(value) -> str:
    """A value as YAML's inline form, which JSON is: emoji and all written as themselves."""
    return json.dumps(value, ensure_ascii=False)


def element_yaml(eid: str, element: dict) -> str:
    """An element as an entry of the settings' `elements:` section: two spaces in, one field a line, each list's
    items one a line, and chess's moves grouped by the piece that makes them."""
    out = [f"  {eid}:"]
    for key, value in element.items():
        if key == "moves" and value and isinstance(value[0], dict):
            out.append("    moves:")
            for group in value:
                out += [f"      - piece: {flow(group['piece'])}", "        list:"]
                out += [f"          - {flow(move)}" for move in group["list"]]
        elif key in ("moves", "history", "people", "leaders"):
            out.append(f"    {key}:" if value else f"    {key}: []")
            out += [f"      - {flow(row)}" for row in value]
        else:
            out.append(f"    {key}: {flow(value)}")
    return "".join(line + "\n" for line in out)


def marks(lines: list[str], name: str) -> tuple[int, int] | None:
    """Where a region's two marker lines stand, or None when neither is there."""
    start = [i for i, line in enumerate(lines) if line.strip() == f"# {name}:start"]
    end = [i for i, line in enumerate(lines) if line.strip() == f"# {name}:end"]
    if not start and not end:
        return None
    if len(start) != 1 or len(end) != 1 or start[0] > end[0]:
        raise ValueError(f"the settings need one '# {name}:start' line, then one '# {name}:end' line, under"
                         " elements:")
    return start[0], end[0]


def section_end(lines: list[str]) -> int:
    """Where a region added to `elements:` goes: after its last entry, before the blank lines and comments that open
    the section after it."""
    top = next((i for i, line in enumerate(lines) if line.rstrip() == "elements:"), None)
    if top is None:
        raise ValueError("the settings have no elements: section to set the boards out in")
    end = next((i for i in range(top + 1, len(lines)) if lines[i].strip() and not lines[i][0].isspace()
                and not lines[i].startswith("#")), len(lines))
    while end > top + 1 and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
        end -= 1
    return end


def set_out(settings: Path, regions: dict[str, list[tuple[str, dict]]]) -> list[str]:
    """Writes each region's elements between its marker lines, adding a region whose markers are missing at the end
    of `elements:`, and writes the file only when something in it changed. Returns the regions that changed, none
    when nothing did."""
    text = settings.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    changed = []
    for name, elements in regions.items():
        body = [line for eid, element in elements for line in element_yaml(eid, element).splitlines(keepends=True)]
        found = marks(lines, name)
        if found is None:
            at = section_end(lines)
            lines[at:at] = [f"  # {name}:start\n", *body, f"  # {name}:end\n"]
            changed.append(name)
        elif lines[found[0] + 1:found[1]] != body:
            lines[found[0] + 1:found[1]] = body
            changed.append(name)
    new = "".join(lines)
    if new != text:
        settings.write_text(new, encoding="utf-8")
    return changed


def load(folder: Path) -> tuple[dict | None, list]:
    """A game's state: the game on its board, or None before its first game, and its Hall of Fame."""
    path, hall = folder / "game.json", folder / "hall-of-fame.json"
    game = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    return game, json.loads(hall.read_text(encoding="utf-8")) if hall.exists() else []


def dump(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"
