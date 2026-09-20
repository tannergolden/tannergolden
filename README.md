<!--
title: "👋 HI, I'M TANNER GOLDEN"
description: 'Profile README for @tannergolden: what I work on, the dispatches this page sends itself, the core repositories and how they fit together, and how to get in touch.'
tags: [profile, ai-research, systems-engineering, automation]
category: profile
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 👋 HI, I'M TANNER GOLDEN

<a name="top"></a>

**The standards and automation that keep a result reproducible after its author moves on.**

_Build it so the right way is the only easy way._

<!-- TYPING:BEGIN -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/typing-dark.svg?v=b2d8e081">
  <img alt="AI research &amp; systems engineering / reproducible by construction / least-privilege CI, pinned to the SHA / standards that outlast their author" src="assets/typing-light.svg?v=3654606b">
</picture>
<!-- TYPING:END -->

[![Status: Active](assets/badges/static/status.svg)](./)
[![Role: Profile](assets/badges/static/role.svg)](./)
[![Context: Automation](assets/badges/static/context.svg)](./)
[![License: MIT](assets/badges/static/license.svg)](./LICENSE)

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

## 📡 Dispatches

Small pieces of the computing record, sent at intervals nobody chose: a character and what it
encodes, an RFC and what it settled, a task solved in a language you have probably never written,
a failure worth remembering.

It is for two readers. One is a developer who would rather find something worth knowing than
another static profile. The other is anyone weighing whether I build automation that holds up
unattended, because that is what this is: a workflow assembling a public page from sources I do not
control, committing the result with nobody pressing anything. The page is the argument, not a
description of one.

Every commit is authored by me and made by the workflow. [How it works](How-It-Works.md) has the
randomness, the sources, and the places this repository departs from the standards the rest of the
account follows.

<!-- DISPATCHES:BEGIN -->
### Sunday, September 20, 2026

[![Dispatch workflow status](assets/badges/dynamic/dispatches.svg?v=10a98963)](https://github.com/tannergolden/tannergolden/actions/workflows/dispatches.yml) [![Dispatches this month](assets/badges/dynamic/month.svg?v=3465b94a)](dispatches/2026/September.md)

| Time | Commit | Dispatch |
| :--- | :--- | :--- |
| 09:28 | `feat(unicode)` | [U+10330 𐌰 GOTHIC LETTER AHSA](dispatches/2026/September.md#dispatch-20260920-092834) |
| 09:28 | `test(sequence)` | [0, 1, 3, 6, 10, 15, 21, 28, what comes next?](dispatches/2026/September.md#dispatch-20260920-092830) |

[All dispatches](dispatches/) · [How it works](How-It-Works.md) · 2 in September
<!-- DISPATCHES:END -->

<!-- MODULES:BEGIN -->
📰 **Show HN** [Airmash - HTML5 Multiplayer Missile Warfare](https://airma.sh/) · 2 points · airma.sh · [discuss](https://news.ycombinator.com/item?id=49775418)  
🧩 **First issue** [Kesavaraja67/telex#36](https://github.com/Kesavaraja67/telex/issues/36) · GFI-5 - Document the risk/review model in the README · Python

> [!TIP]
> **docker-compose-down**: Stop and remove all containers and networks ([tldr](https://github.com/tldr-pages/tldr/blob/main/pages/common/docker-compose-down.md))
>
> ```bash
> docker compose down
> ```
<!-- MODULES:END -->

---

## 📦 Repositories

These are one system rather than a portfolio; each repository has a single job.

| Repository                                                     | What it is                                                                            |
| :------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| [`standards`](https://github.com/tannergolden/standards)       | Reusable workflows and the documented standards they enforce                          |
| [`path`](https://github.com/tannergolden/path)                 | Repository template: structure, health files and wiring, already decided              |
| [`intelligence`](https://github.com/tannergolden/intelligence) | Agent instructions, published once and pinned rather than pasted into each repository |
| [`emblems`](https://github.com/tannergolden/emblems)           | Badges a repository draws for itself, so no README depends on an image service        |
| [`.github`](https://github.com/tannergolden/.github)           | Default community health files for repositories that do not ship their own            |
| [`dotfiles`](https://github.com/tannergolden/dotfiles)         | Shell, editor, and toolchain configuration, installed the same way everywhere         |
| [`tannergolden`](https://github.com/tannergolden/tannergolden) | This file, and the workflow that keeps it current                                     |

A repository that runs a pipeline holds a short trigger stub, and the logic, the configuration, and
the standards it uses live in `standards` and are pulled in by reference: called, never copied. A
trigger has nothing in it to go stale, so nothing downstream ages. This repository is the documented
exception: a profile, not a pipeline, and its one workflow lives here.

---

## 🧰 Stack

| Area           | Tools                                                                                                                                                                                                                                          |
| :------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Languages**  | ![Python](assets/badges/static/stack-python.svg) ![Bash](assets/badges/static/stack-bash.svg) ![JavaScript](assets/badges/static/stack-javascript.svg)                                                                                     |
| **Tooling**    | ![GitHub Actions](assets/badges/static/stack-actions.svg) ![Make](assets/badges/static/stack-make.svg) ![Ruff](assets/badges/static/stack-ruff.svg) ![pytest](assets/badges/static/stack-pytest.svg) ![Prettier](assets/badges/static/stack-prettier.svg) |
| **Operations** | ![CodeQL](assets/badges/static/stack-codeql.svg) ![Dependabot](assets/badges/static/stack-dependabot.svg) ![Gitleaks](assets/badges/static/stack-gitleaks.svg) ![SBOM](assets/badges/static/stack-sbom.svg)                               |

<!-- CARDS:BEGIN -->
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/stats-dark.svg?v=809d4bda">
  <img alt="GitHub statistics for tannergolden: 5 public repositories, 0 stars, 11 followers, 775 commits and 0 pull requests in 2026." src="assets/stats-light.svg?v=a95d2feb">
</picture>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/languages-dark.svg?v=e3f6adf8">
  <img alt="Top languages across public repositories: Python 87.6%, Shell 10.7%, Makefile 0.9%, JavaScript 0.8%." src="assets/languages-light.svg?v=d8c13bb2">
</picture>
<!-- CARDS:END -->

---

## 📫 Elsewhere

| Where        | Link                                                         |
| :----------- | :----------------------------------------------------------- |
| **Website**  | [tannergolden.com](https://www.tannergolden.com)             |
| **LinkedIn** | [in/tannergolden](https://www.linkedin.com/in/tannergolden/) |

Open to conversations about AI infrastructure, reproducibility, and developer tooling.

---

Dispatch sources: Wikidata (CC0) · Unicode · RFC Editor · OEIS (CC BY-SA) · Rosetta Code (GFDL) ·
Wikipedia (CC BY-SA) · tldr-pages (CC BY) · Hacker News · GitHub. Terms in
[`NOTICE`](NOTICE). Every image on this page is a committed file; nothing is fetched from an image
service.

<!-- UPDATED:BEGIN -->
Last updated 10:05 EDT on Sunday, September 20, 2026.
<!-- UPDATED:END -->

<div align="center">

**Built to outlast the attention that built it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden).

</div>
