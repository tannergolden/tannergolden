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
guardrails, and standards that decide whether a result can be reproduced next week, on another
machine, by someone who was not there the first time.

That gap is where most of my work sits. Research code accumulates quiet assumptions about the
machine it was written on, and those assumptions tend to surface late, usually when somebody else
needs the result and the person who produced it has moved on. I build the environments, continuous
integration, and documentation standards that surface them early instead, and I spend most of my
effort making the correct path the one that takes the least work.

---

## 🛠️ What I Build

- 🤖 **AI-native infrastructure.** Repositories and pipelines set up so that engineers and coding
  agents both start with the project's rules already loaded, rather than discovering them in review.
- 🛡️ **Security-first automation.** Least-privilege continuous integration, third-party actions
  pinned to commit SHAs, an explicit supply-chain posture, and licensing metadata that holds up to
  an audit.
- ⚙️ **Reproducible environments.** Toolchains and command-line tooling built so that the same
  inputs produce the same outputs on someone else's hardware, including the GPU-bound work where
  that is hardest to guarantee.
- 📝 **Enforced documentation.** Standards written as machine-checked, indexed guides that a gate
  verifies on every change, which keeps the written rule and the enforced rule the same rule.

---

## 🧭 How I Build

These are the working principles I hold to, and the ones I look for in the people I build alongside:

- **Standards over opinions.** The documented rule holds until a pull request changes it, which
  keeps design decisions in the repository and out of the review thread.
- **Machined, not memorized.** If a rule matters, something enforces it automatically. Rules that
  depend on recall drift, and the drift is hardest to notice in the weeks it matters most.
- **Small diffs, green gates.** Changes ship tested, reviewed, and reversible, so a wrong call costs
  a revert rather than a release.
- **Evidence over badges.** Claims carry evidence. A green check that measures nothing is worse than
  no check at all, because it buys confidence that nothing has earned.
- **Defaults are policy.** Most people never change a default, so the default is the real decision.
  I spend disproportionate effort there.

---

## 🌿 How I Work With Others

- **Review is for correctness, security, and fit with the established pattern.** Style is the
  formatter's job, which leaves the review for the parts that actually break.
- **Written first.** Decisions land in the repository rather than in a thread that scrolls away, so
  the reasoning is still there for whoever picks the work up next.
- **Bias toward reversibility.** I would rather ship something narrow and undo it cheaply than ship
  something broad and spend a quarter negotiating its removal.
- **The tooling is the handover.** Most of what I build exists so that someone else can run the work
  without me in the room, and I treat a colleague stuck on my setup as a defect in the setup.

---

## 📦 The Core Repositories

These are not a portfolio of unrelated projects. They are one system, each repository with a single
job, wired so that a fix lands once and reaches everything downstream of it. Common threads:
hardened continuous integration, enforced documentation standards, and infrastructure that keeps
itself current instead of aging into a snapshot of the day it was written.

| Repository                                                     | What it is                                                                                          |
| :------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------- |
| [`standards`](https://github.com/tannergolden/standards)       | The engine. Reusable workflows, composite actions, and the documented standards they enforce        |
| [`path`](https://github.com/tannergolden/path)                 | The template. Structure, health files, and wiring, all decided and ready to build on                |
| [`intelligence`](https://github.com/tannergolden/intelligence) | Agent instructions, published once and pinned, rather than pasted into every repository             |
| [`.github`](https://github.com/tannergolden/.github)           | The account's default community health files, for repositories that do not ship their own           |
| [`dotfiles`](https://github.com/tannergolden/dotfiles)         | The workstation. Shell, editor, and toolchain configuration, installed the same way everywhere      |
| [`tannergolden`](https://github.com/tannergolden/tannergolden) | This file                                                                                           |

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
> **The core repositories take the conventions and not the automation.** `.github`, `dotfiles`,
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
