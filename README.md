<!--
title: "👋 HI, I'M TANNER GOLDEN"
description: "Profile README for @tannergolden: what I work on, the developer news this page posts by itself, how the repositories fit together, and how to reach me."
tags: [profile, ai-research, systems-engineering, automation]
category: profile
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 👋 HI, I'M TANNER GOLDEN

<a name="top"></a>

**I build the automation and standards that keep things working after the person who built them moves on.**

_If the right way is the easy way, people take it._

[![Status: Active](assets/badges/static/status.svg)](./)
[![Role: Profile](assets/badges/static/role.svg)](./)
[![Context: Automation](assets/badges/static/context.svg)](./)
[![License: MIT](assets/badges/static/license.svg)](./LICENSE)

<!-- AVAILABILITY:BEGIN -->
[![Availability: Open to consult](assets/badges/dynamic/availability.svg?v=c5ab6191)](./)
<!-- AVAILABILITY:END -->

</div>

---

## 💡 About

I work on the plumbing that makes AI research hold up. Pipelines, guardrails, the standards that
decide whether a result still runs next week, on a different machine, for someone who wasn't there
the first time.

Research code quietly picks up assumptions about the machine it was written on, and you usually
find out too late. My job is to surface them early. In practice that means CI with the smallest
permissions that work, third-party actions pinned to a commit SHA instead of a tag, and rules
something actually checks on every change rather than rules people are asked to remember.

---

## 📡 Dispatch

Developer news a workflow finds and commits on its own. I wrote it, I don't run it.
[How it works](How-It-Works.md).

<!-- DISPATCHES:BEGIN -->
### Sunday, September 20, 2026

[![Dispatch workflow status](assets/badges/dynamic/dispatches.svg?v=10a98963)](https://github.com/tannergolden/tannergolden/actions/workflows/dispatches.yml) [![Dispatches this month](assets/badges/dynamic/month.svg?v=b5435749)](dispatches/2026/September.md)

| Time | Commit | Dispatch |
| :--- | :--- | :--- |
| 19:05 | `feat(trending)` | [Tencent/WeMM-Embedding](dispatches/2026/September.md#dispatch-20260920-190522) |
| 18:41 | `docs(rfc)` | [RFC 9792: Prefix Flag Extension for OSPFv2 and OSPFv3](dispatches/2026/September.md#dispatch-20260920-184118) |
| 18:38 | `security(advisory)` | [GHSA-c8w2-fgvx-vhv4: github.com/kcp-dev/kcp](dispatches/2026/September.md#dispatch-20260920-183803) |

[All dispatches](dispatches/) · [How it works](How-It-Works.md) · 3 in September
<!-- DISPATCHES:END -->

<!-- MODULES:BEGIN -->
> [!TIP]
> **sed** · Edit text in a scriptable manner. · [tldr](https://github.com/tldr-pages/tldr/blob/main/pages/common/sed.md)
>
> Replace all apple (basic regex) occurrences with mango (basic regex) in all input lines and print the result to stdout:
>
> ```bash
> <command> | sed 's/apple/mango/g'
> ```
<!-- MODULES:END -->

---

## 📦 Repositories

Not a portfolio. These fit together as one system, and each one does a single job.

| Repository                                                     | What it is                                                                            |
| :------------------------------------------------------------- | :------------------------------------------------------------------------------------ |
| [`standards`](https://github.com/tannergolden/standards)       | Reusable workflows and the documented standards they enforce                          |
| [`path`](https://github.com/tannergolden/path)                 | Repository template: structure, health files and wiring, already decided              |
| [`intelligence`](https://github.com/tannergolden/intelligence) | Agent instructions, published once and pinned rather than pasted into each repository |
| [`emblems`](https://github.com/tannergolden/emblems)           | Badges a repository draws for itself, so no README depends on an image service        |
| [`.github`](https://github.com/tannergolden/.github)           | Default community health files for repositories that do not ship their own            |
| [`dotfiles`](https://github.com/tannergolden/dotfiles)         | Shell, editor, and toolchain configuration, installed the same way everywhere         |
| [`tannergolden`](https://github.com/tannergolden/tannergolden) | This file, and the workflow that keeps it current                                     |

When one of these runs a pipeline, all it holds is a short trigger. The logic, the config and the
standards live in `standards` and get called from there, never copied in. So there's nothing in the
trigger to go stale, and fixing something once fixes it everywhere. This repo is the exception, and
it's written down as one: it's a profile rather than a pipeline, so its workflow lives here.

---

## 🧰 Stack

What I reach for most. Mostly boring choices, picked because they are boring.

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

Happy to talk about AI infrastructure, reproducibility, or developer tooling. The badge at the
top says whether I'm looking for work right now.

---

Dispatch sources: Hacker News · GitHub · Lobsters · tldr-pages (CC BY), with the full terms in
[`NOTICE`](NOTICE). Every image here is a file in this repo, so loading the page fetches nothing
from an image service.

<!-- UPDATED:BEGIN -->
Last updated 19:33 EDT on Sunday, September 20, 2026.
<!-- UPDATED:END -->

<div align="center">

**Built to keep working after I stop paying attention to it.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by [@tannergolden](https://github.com/tannergolden).

</div>
