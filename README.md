<!--
title: '👋 AI RESEARCH & SYSTEMS ENGINEERING'
description: 'Profile README for @tannergolden, covering what I work on, the core repositories and how they fit together, and how to get in touch.'
tags: [profile, ai-research, systems-engineering, reproducibility]
category: profile
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 👋 AI RESEARCH & SYSTEMS ENGINEERING

<a name="top"></a>

**The standards and automation that keep a result reproducible after its author moves on.**

_Build it so the right way is the only easy way._

</div>

---

## 💡 About

I work at the boundary between AI research and the systems that make it hold up: the pipelines,
guardrails, and standards that decide whether a result can be reproduced next week, on another
machine, by someone who was not there the first time.

Research code accumulates quiet assumptions about the machine it was written on, and those
assumptions surface late. I build the environments and documentation standards that surface them
early. The recurring concerns are least-privilege continuous integration, third-party actions
pinned to commit SHAs, and rules a gate checks on every change.

---

## 📦 Repositories

These are one system rather than a portfolio; each repository has a single job.

| Repository                                                     | What it is                                                                            |
| :------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| [`standards`](https://github.com/tannergolden/standards)       | Reusable workflows and the documented standards they enforce                          |
| [`path`](https://github.com/tannergolden/path)                 | Repository template: structure, health files and wiring, already decided              |
| [`intelligence`](https://github.com/tannergolden/intelligence) | Agent instructions, published once and pinned rather than pasted into each repository |
| [`.github`](https://github.com/tannergolden/.github)           | Default community health files for repositories that do not ship their own            |
| [`dotfiles`](https://github.com/tannergolden/dotfiles)         | Shell, editor, and toolchain configuration, installed the same way everywhere         |
| [`tannergolden`](https://github.com/tannergolden/tannergolden) | This file                                                                             |

A repository that runs a pipeline holds a short trigger stub, and the logic, the configuration, and
the standards it uses live in `standards` and are pulled in by reference: called, never copied. A
trigger has nothing in it to go stale, so nothing downstream ages.

---

## 📫 Elsewhere

| Where        | Link                                                         |
| :----------- | :----------------------------------------------------------- |
| **Website**  | [tannergolden.com](https://www.tannergolden.com)             |
| **LinkedIn** | [in/tannergolden](https://www.linkedin.com/in/tannergolden/) |

Open to conversations about AI infrastructure, reproducibility, and developer tooling.

---

<div align="center">

**Built to outlast the attention that built it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden).

</div>
