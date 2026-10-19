<!--
title: '⚙️ WORKFLOWS'
description: 'Every workflow on the profile: the games, the clock that keeps their time, the runs that draw the page, and the tests.'
type: index
keywords: [github-actions, workflows, games]
-->

<div align="center">

# ⚙️ WORKFLOWS

<a name="top"></a>

**What runs the games, and what draws the page.**

_Every move arrives through the Arbiter._

</div>

---

## 💡 What This Folder Is For

Every workflow on the profile. Each game's own workflow only plays moves, and
is started through the Official Arbiter from tannergolden/play's Move Intake;
[`clock.yml`](clock.yml) keeps the time for all four. The others draw the page
on their schedules, and [`games-tests.yml`](games-tests.yml) runs the tests when
a script or a game's workflow changes.

Never start a game's workflow by hand: every move reaches it as an issue in
tannergolden/play.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log fields=name,on -->

| Entry                                | Name               | Triggers                                                                                                                                                                                                                                                                                                               | Purpose    |
| :----------------------------------- | :----------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------- |
| [`checkers.yml`](checkers.yml)       | Checkers           | `workflow_dispatch`                                                                                                                                                                                                                                                                                                    | -          |
| [`chess.yml`](chess.yml)             | Chess              | `workflow_dispatch`                                                                                                                                                                                                                                                                                                    | -          |
| [`clock.yml`](clock.yml)             | Clock              | `schedule` (`17,47 * * * *`), `workflow_dispatch`                                                                                                                                                                                                                                                                      | -          |
| [`game.yml`](game.yml)               | Game               | `workflow_call`                                                                                                                                                                                                                                                                                                        | -          |
| [`games-tests.yml`](games-tests.yml) | Games Tests        | `push` (`.github/scripts/*.py`, `.github/scripts/arbiter.sh`, `.github/workflows/chess.yml`, `.github/workflows/tictac.yml`, `.github/workflows/pentago.yml`, `.github/workflows/checkers.yml`, `.github/workflows/game.yml`, `.github/workflows/clock.yml`, `.github/workflows/games-tests.yml`), `workflow_dispatch` | -          |
| [`markdown.yml`](markdown.yml)       | &#x1F4DD; Markdown | `schedule` (`0 5 * * *`), `workflow_dispatch`                                                                                                                                                                                                                                                                          | -          |
| [`notes.yml`](notes.yml)             | Notes              | `schedule` (`30 14 * * 1`), `workflow_dispatch`                                                                                                                                                                                                                                                                        | -          |
| [`pentago.yml`](pentago.yml)         | Pentago            | `workflow_dispatch`                                                                                                                                                                                                                                                                                                    | -          |
| [`picks.yml`](picks.yml)             | Picks              | `schedule` (`30 14 * * 3`, `30 14 * * 5`), `workflow_dispatch`                                                                                                                                                                                                                                                         | -          |
| [`README.md`](README.md)             | -                  | -                                                                                                                                                                                                                                                                                                                      | This file. |
| [`tictac.yml`](tictac.yml)           | Tic-Tac            | `workflow_dispatch`                                                                                                                                                                                                                                                                                                    | -          |

<!-- AUTO-INDEX:END -->

This log is drawn from each workflow's own `name:` and triggers. Redraw this log
in the same commit as a change to this folder, from a checkout of
tannergolden/standards at `v1`:

```bash
python3 <standards>/.github/scripts/update-doc-indexes.py --tree --write
```

---

<div align="center">

**The games play themselves, one move at a time.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
