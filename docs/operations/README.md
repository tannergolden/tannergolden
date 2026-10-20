<!--
title: '🛡️ OPERATIONS & SECURITY'
description: 'Keeping this project healthy and safe once it runs: runbooks, incident response, post-mortems, security, and the risks it still carries.'
type: index
keywords: [operations, security]
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🛡️ OPERATIONS & SECURITY

<a name="top"></a>

**Keeping this project healthy and safe.**

_What to do while it runs, and when it breaks._

</div>

---

## 💡 What This Folder Is For

What it takes to keep this project running once it exists, and what to do when
something goes wrong.

- **Runbooks**: the steps for a routine task or a known failure, written to be
  followed under pressure.
- **Incidents**: how one is declared and handled, and who is told.
- **Post-mortems**: one for each incident, in `post-mortems/`.
- **Security**: what this project protects, how it protects it, and the risks
  it still carries.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                                      | Purpose                                                                                                                                                                                                                                                             |
| :----------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| [`README.md`](README.md)                   | This file.                                                                                                                                                                                                                                                          |
| [`Troubleshooting.md`](Troubleshooting.md) | What to do when a move is not ruled on or gets no reply, a board is not redrawn, the Arbiter moves late, or a run fails on a game's state or the settings: each symptom, what the run log says, and the way back. Read it when anything on the profile looks stuck. |

<!-- AUTO-INDEX:END -->

The standards' indexer draws this log from each document's own frontmatter:
redraw it in the same commit as a change to the folder.

---

## 🔗 See also

- [Documentation index](../README.md) - every document this project keeps
- [Operations & Security](https://github.com/tannergolden/standards/blob/Development/docs/operations/README.md) - the shared guardrails: protection, dependencies, secrets and troubleshooting

---

<div align="center">

**Write the runbook before the night you need it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
