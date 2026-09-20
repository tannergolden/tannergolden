<!--
title: "👋 HI, I'M TANNER GOLDEN"
description: 'Profile README for @tannergolden: what I work on, a journal this page writes for itself, the core repositories and how they fit together, and how to get in touch.'
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

## 📓 Journal

This section is kept by GitHub Actions. At moments drawn from an exponential distribution, never
on a schedule, a workflow adds one entry to the [journal](journal/) and commits it. Every commit is
authored by me and made by the workflow; [How it works](How-It-Works.md) has the details, the
randomness, and the places this repository departs from the standards the rest of the account
follows.

<!-- JOURNAL:BEGIN -->
### Sunday, September 20, 2026

[![Journal workflow status](assets/badges/dynamic/journal.svg)](https://github.com/tannergolden/tannergolden/actions/workflows/journal.yml) [![Entries this month](assets/badges/dynamic/month.svg)](journal/)

_No entries yet. The first one lands at a random moment within the next twelve hours or so; nothing here is on a schedule._

[Full journal](journal/) · [How it works](How-It-Works.md) · 0 entries in September
<!-- JOURNAL:END -->

<!-- MODULES:BEGIN -->
_The daily modules fill in on the first refresh._
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
  <source media="(prefers-color-scheme: dark)" srcset="assets/stats-dark.svg?v=7574aa03">
  <img alt="GitHub statistics for tannergolden: n/a public repositories, n/a stars, n/a followers, n/a commits and n/a pull requests in 2026." src="assets/stats-light.svg?v=d47f8e7c">
</picture>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/languages-dark.svg?v=478f6e36">
  <img alt="Top languages across public repositories: no data yet." src="assets/languages-light.svg?v=6139e4a2">
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

Journal sources: Wikidata (CC0) · Unicode · RFC Editor · xkcd (CC BY-NC) · OEIS (CC BY-SA) ·
Rosetta Code (GFDL) · Wikipedia (CC BY-SA) · tldr-pages (CC BY) · Hacker News · GitHub. Terms in
[`NOTICE`](NOTICE). Every image on this page is a committed file; nothing is fetched from an image
service.

<!-- UPDATED:BEGIN -->
Last updated 02:54 EDT on Sunday, September 20, 2026.
<!-- UPDATED:END -->

<div align="center">

**Built to outlast the attention that built it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden).

</div>
