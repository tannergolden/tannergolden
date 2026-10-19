<!--
title: '📝 NOTES'
description: 'The five files of notes the Field Notes draw from, one for each kind of GitHub alert, 1,000 notes in each.'
type: index
keywords: [notes, alerts, field-notes]
-->

<div align="center">

# 📝 NOTES

<a name="top"></a>

**Five kinds of alert, a thousand notes each.**

_One of each kind, every Monday._

</div>

---

## 💡 What This Folder Is For

Five files of notes, one for each kind of GitHub alert the profile's Field
Notes show: a caution, an important point, a note, a tip and a warning. Each
holds 1,000 notes, 250 for each level. Every Monday,
[`notes.py`](../scripts/notes.py) redraws the Field Notes through
[`notes.yml`](../workflows/notes.yml), one alert of each kind, and a coin seeded
by the week decides whether each comes from here or from a public dataset.

Every note added makes the rotation longer. The script refuses an en or em
dash in a note, so write without them.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log -->

| Entry                              | Purpose                                                                                                 |
| :--------------------------------- | :------------------------------------------------------------------------------------------------------ |
| [`caution.toml`](caution.toml)     | Caution: something hard to undo. An action that is destructive, irreversible or security-critical.      |
| [`important.toml`](important.toml) | Important: something that matters. A practice whose absence causes real damage over time.               |
| [`note.toml`](note.toml)           | Note: something to know. A fact or concept that changes how you think about a tool or practice.         |
| [`README.md`](README.md)           | This file.                                                                                              |
| [`tip.toml`](tip.toml)             | Tip: something to try. A concrete technique, command or habit with an immediate payoff.                 |
| [`warning.toml`](warning.toml)     | Warning: something to watch for. A pitfall, surprising behavior or common mistake, and how to avoid it. |

<!-- AUTO-INDEX:END -->

Redraw this log in the same commit as a change to this folder, from a checkout
of tannergolden/standards at `v1`:

```bash
python3 <standards>/.github/scripts/update-doc-indexes.py --tree --write
```

---

<div align="center">

**Five alerts a week, from a thousand of each kind.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
