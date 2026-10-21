<!--
title: '🛠️ TECHNICAL'
description: 'How this project is built: its architecture, stack and source, one document for each part that needs one, and the designs, plans and research behind them.'
type: index
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🛠️ TECHNICAL

<a name="top"></a>

**How this project is built.**

_Written down where the code cannot say it._

</div>

---

## 💡 What This Folder Is For

How this project is built: its architecture and how its parts fit, the stack it
runs on and where its source lives, and one document for each part that needs
one.

- **The stack and the source**: what the project is built with, and where each
  part of it lives.
- **One folder per area**, such as `backend/`, `infrastructure/` or `testing/`.
- **Designs, plans and research**: `designs/`, `plans/` and `research/`.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                                  | Purpose                                                                                                                                                                                                                                                                           |
| :----------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`How-The-Games-Run.md`](How-The-Games-Run.md)         | How a move travels from its issue on tannergolden/play to its ruling and the redraw, how the engine decides it, how the clock keeps every game's week, and what a game module gives the shared engine. Read it before changing a game's workflow, its script or arbiter.sh.       |
| [`How-The-Page-Is-Drawn.md`](How-The-Page-Is-Drawn.md) | How README.md is put together: the blocks the Markdown Kit draws and the settings it reads, the regions the games and the pickers write, the weekly placards, and the Field Notes with their library. Read it before editing README.md, .github/markdown.yaml or a file of notes. |
| [`README.md`](README.md)                               | This file.                                                                                                                                                                                                                                                                        |

<!-- AUTO-INDEX:END -->

The standards' indexer draws this log from each document's own frontmatter:
redraw it in the same commit as a change to the folder.

---

## 🔗 See also

- [Documentation index](../README.md) - every document this project keeps

---

<div align="center">

**Write down what the code cannot say.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
