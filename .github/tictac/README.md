<!--
title: '❌ TIC-TAC STATE'
description: 'The Tic-Tac game in progress on the profile, kept in game.json, which is written each time a move is played and never by hand.'
type: index
-->

<div align="center">

# ❌ TIC-TAC STATE

<a name="top"></a>

**The game in progress, in one file.**

_Written each time a move is played, never by hand._

</div>

---

## 💡 What This Folder Is For

[`game.json`](game.json) is the Tic-Tac game being played on the profile: its
number, when it started, the side the Arbiter drew to place the first ghost, the
ghosts placed, and every move so far. It is written each time a move is played:
by [`tictac.yml`](../workflows/tictac.yml) for a player's move, and by
[`clock.yml`](../workflows/clock.yml) for a move the Arbiter makes when a side
has gone a week without moving, or for a fresh board. Nothing else writes it, so
never edit it by hand.

How a move is played and how a game ends are in the
[Tic-Tac](../../docs/library/Tic-Tac.md) guide, and every field of the game's
files in [Game State](../../docs/references/Game-State.md).

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                    | Purpose                                                        |
| :----------------------- | :------------------------------------------------------------- |
| [`game.json`](game.json) | The Tic-Tac game in progress, as the last move played left it. |
| [`README.md`](README.md) | This file.                                                     |

<!-- AUTO-INDEX:END -->

A JSON file cannot describe itself, so its row is written by hand, and redrawing
the log keeps it. Redraw it in the same commit as a change to this folder, from
a checkout of tannergolden/standards at `v1`:

```bash
python3 <standards>/.github/scripts/update-doc-indexes.py --tree --write
```

---

<div align="center">

**One game at a time, every move kept.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
