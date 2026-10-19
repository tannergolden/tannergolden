<!--
title: '♟️ CHESS STATE'
description: 'The Chess game in progress on the profile, kept in game.json, which is written each time a move is played and never by hand.'
type: index
keywords: [chess, state, games]
-->

<div align="center">

# ♟️ CHESS STATE

<a name="top"></a>

**The game in progress, in one file.**

_Written each time a move is played, never by hand._

</div>

---

## 💡 What This Folder Is For

[`game.json`](game.json) is the Chess game being played on the profile: its
number, when it started, the position in FEN, and every move so far. It is
written each time a move is played: by [`chess.yml`](../workflows/chess.yml) for
a player's move, and by [`clock.yml`](../workflows/clock.yml) for a move the
Arbiter makes when a side has gone a week without moving, or for a fresh board.
Nothing else writes it, so never edit it by hand.

How a move is played and how a game ends are in the [Chess](../../docs/Chess.md)
guide.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                    | Purpose                                                      |
| :----------------------- | :----------------------------------------------------------- |
| [`game.json`](game.json) | The Chess game in progress, as the last move played left it. |
| [`README.md`](README.md) | This file.                                                   |

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
