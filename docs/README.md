<!--
title: '📚 DOCUMENTATION'
description: 'Every document the profile keeps, in the seven folders the standards keep: the games'' guides in library/, and how the games and the page run, and what to do when they stick, in the others.'
type: index
keywords: [documentation, games]
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 📚 DOCUMENTATION

<a name="top"></a>

**Every document the profile keeps, in the seven folders the standards keep.**

_Start with the games._

</div>

---

## 🎲 Start With The Games

[Games](library/Games.md) says how to play the four games on the profile
against @tannergolden: making a move, whose turn it is, the clock and the
Arbiter, and what happens when a game ends. Each game's own guide sits beside
it, with its rules, how its moves are written and how its games end:
[Chess](library/Chess.md), [Checkers](library/Checkers.md),
[Pentago](library/Pentago.md) and [Tic-Tac](library/Tic-Tac.md).

---

## 🚀 Running The Profile

For the owner, a maintainer or an agent about to change something here:

- [Overview](introduction/Overview.md): what lives where, which run writes
  each file, and how to work here.
- [How The Games Run](technical/How-The-Games-Run.md): a move from its issue
  to its ruling and the redraw, the engines and the clock.
- [How The Page Is Drawn](technical/How-The-Page-Is-Drawn.md): the kit's
  blocks and settings, the placards and the Field Notes.
- [Game State](references/Game-State.md): every file a game keeps, and the
  regions of the settings it writes.
- [Workflows & Schedules](references/Workflows-&-Schedules.md): when each run
  comes, what it may write, its secrets and its commits.
- [Troubleshooting](operations/Troubleshooting.md): a move not ruled on, a
  board not redrawn, a run that fails, and the way back.

---

## 📁 The Seven Folders

The profile's documents sit in the same seven folders as the
[standards' own](https://github.com/tannergolden/standards/blob/Development/docs/README.md),
so every repository on the standards reads the same way:

```bash
docs/
├── introduction/        # where to start: overview, principles, setup, roadmap
├── distribution/        # from a branch to a release: releasing, delivery
├── technical/           # how it is built: architecture, source, designs, plans
├── operations/          # keeping it healthy and safe: runbooks, post-mortems
├── references/          # things to look up: glossary, catalogues, formats
├── library/             # what to learn: the games' guides
└── adrs/                # architecture decision records
```

Each folder carries a `README.md` that says what belongs in it and logs its
files. Put each new document in the folder its kind names, and redraw the logs
in the same commit.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                     | Purpose                                                                                                                                                     |
| :---------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`adrs/`](adrs/README.md)                 | Architecture decision records, one file per decision, each logged with its status, date and evidence.                                                       |
| [`distribution/`](distribution/README.md) | From a branch to a release: how a change moves through this project and how a release reaches its users, wherever this project adds to the shared workflow. |
| [`introduction/`](introduction/README.md) | Where to start: what this project is and how its parts fit together, the principles it holds to, how to get ready to work on it, and where it is going.     |
| [`library/`](library/README.md)           | What to learn, and where: guides, background and further reading for anyone new to this project's domain or its tools.                                      |
| [`operations/`](operations/README.md)     | Keeping this project healthy and safe once it runs: runbooks, incident response, post-mortems, security, and the risks it still carries.                    |
| [`references/`](references/README.md)     | Things to look up: the glossary, catalogues, settings and formats, the pages this project consults rather than reads through.                               |
| [`technical/`](technical/README.md)       | How this project is built: its architecture, stack and source, one document for each part that needs one, and the designs, plans and research behind them.  |
| [`README.md`](README.md)                  | This file.                                                                                                                                                  |

<!-- AUTO-INDEX:END -->

---

<div align="center">

**One move at a time.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
