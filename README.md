<!--
title: '👋 HELLO WORLD'
description: 'Profile README for @tannergolden, covering focus areas, engineering principles, the core repositories and how they fit together, and how to get in touch.'
tags: [profile, ai-research, systems-engineering, reproducibility]
category: profile
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 👋 HELLO WORLD

<a name="top"></a>

**AI research and systems engineering. Reproducibility by default.**

_Build it so the right way is the only easy way._

</div>

---

## 💡 About

I work at the boundary between AI research and the systems that make it hold up: the pipelines,
guardrails, and standards that decide whether a result can be reproduced next week by someone else,
on another machine, without the original author in the room.

Most of what I build exists because that gap is where good work quietly dies. A model that cannot be
rerun is an anecdote. A pipeline that only its author can operate is a liability. A standard that
lives in someone's head is already out of date. The interesting engineering problem is not producing
the result, it is making the result survive contact with time, tooling, and other people.

---

## 🛠️ What I Build

- 🤖 **AI-native infrastructure.** Repositories, pipelines, and guardrails designed so that frontier
  models and human engineers both do their best work by default, steered by machine-loaded rules
  instead of by memory or convention.
- 🛡️ **Security-first automation.** Least-privilege continuous integration, third-party actions
  pinned to commit SHAs, an explicit supply-chain posture, and licensing metadata that survives an
  audit rather than one that merely exists.
- ⚙️ **Reproducible environments.** Toolchains and command-line tooling built so that the same
  inputs produce the same outputs on someone else's hardware, including the GPU-bound work where
  that is hardest to guarantee.
- 📝 **Documentation as law.** Standards written as machine-checked, indexed guides that a gate
  enforces on every change, rather than prose that rots politely in a wiki.

---

## 🧭 How I Build

These are the working principles I hold to, and the ones I look for in the people I build alongside:

- **Standards over opinions.** The documented rule wins until a pull request changes it. Seniority
  is not an argument.
- **Machined, not memorized.** If a rule matters, something enforces it automatically. Quality that
  depends on everyone remembering is quality that degrades the first busy week.
- **Small diffs, green gates.** Changes ship tested, reviewed, and reversible. A change nobody can
  revert safely is a change nobody should have merged.
- **Verified over vanity.** Claims carry evidence. A green badge that measures nothing is worse than
  no badge, because it buys false confidence.
- **Defaults are policy.** Most people never change a default, so the default is the real decision.
  I spend disproportionate effort there.

---

## 🌿 How I Work With Others

- **Review is for correctness, security, and fit with the established pattern.** Style is the
  formatter's job, and I would rather spend the review on the thing that actually breaks.
- **Written first.** Decisions land in the repository, not in a thread that scrolls away. If a
  choice mattered enough to argue about, it matters enough to record.
- **Bias toward reversibility.** I would rather ship something narrow and undo it cheaply than ship
  something broad and negotiate its removal for a quarter.

---

## 📦 The Core Repositories

These are not a portfolio of unrelated projects. They are one system, each repository with a single
job, wired so that a fix lands once and reaches everything downstream of it. Common threads:
hardened continuous integration, enforced documentation standards, and infrastructure that keeps
itself current instead of aging into a snapshot of the day it was written.

| Repository                                                        | What it is                                                                                          |
| :---------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| [📐 `standards`](https://github.com/tannergolden/standards)       | The engine. Reusable workflows, composite actions, and the documented standards they enforce        |
| [🛤️ `path`](https://github.com/tannergolden/path)                 | The template. Structure, health files, and wiring, all decided and ready to build on                |
| [🤖 `intelligence`](https://github.com/tannergolden/intelligence) | Agent instructions, published once and pinned, rather than pasted into every repository             |
| [🛡️ `.github`](https://github.com/tannergolden/.github)           | The account's default community health files, for repositories that do not ship their own           |
| [👋 `tannergolden`](https://github.com/tannergolden/tannergolden) | This file                                                                                           |

### 🌿 How they fit together

**One rule holds the system up: called, never copied.** A repository that runs a pipeline holds a
short trigger stub naming the events it cares about, and nothing else. The logic, the scripts, the
linter configuration, and the standards themselves live in `standards` and are pulled in by
reference. A trigger has nothing in it to go stale, so nothing downstream ages.

That rule is what makes the template worth using. Generating from `path` gives you a repository that
is already wired, and the wiring keeps improving after you generate, precisely because you were
never handed a copy of it.

The two halves arrive differently, and that is deliberate. Structure comes as real folders, yours to
change from the first commit, because only you can decide what the project becomes. Standards come
as links, never copies, because a standard pasted into a repository starts going stale the moment it
lands. What you own, you own outright; what is shared stays shared.

Community health files are the one thing `path` copies rather than inherits, and that is the same
reasoning applied to a case where it points the other way. Account defaults reach the repositories
inside the account; a repository generated from a public template may not live in this account at
all, so a default here would never travel with it. A template meant for other people has to hand
over a repository that is complete on its own, not one that only looks complete from the inside.

> [!NOTE]
> **The core repositories take the conventions and not the automation.** `.github`,
> `intelligence`, and this profile hold no project to lint, test or build, so they follow the
> documented standards by link without installing the gate set. "Called, never copied" describes how
> the automation reaches the repositories that run it, not a claim that every repository runs it.

---

## 📫 Elsewhere

| Where        | Link                                                         |
| :----------- | :----------------------------------------------------------- |
| **Website**  | [tannergolden.com](https://www.tannergolden.com)             |
| **LinkedIn** | [in/tannergolden](https://www.linkedin.com/in/tannergolden/) |

Open to conversations about AI infrastructure, reproducibility, and developer tooling. The fastest
route is a message on either of the above.

---

<div align="center">

**Built to outlast the attention that built it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden).

</div>
