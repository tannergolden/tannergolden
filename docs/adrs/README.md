<!--
title: '🧭 ARCHITECTURE DECISIONS'
description: 'Architecture decision records, one file per decision, each logged with its status, date and evidence.'
type: index
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🧭 ARCHITECTURE DECISIONS

<a name="top"></a>

**Every significant decision this project has made, and why, one record each.**

_One decision per record. One row per decision._

</div>

---

## 💡 What This Folder Is For

An architecture decision record (ADR) captures one significant decision: the
context it was made in, the options weighed, and the consequences accepted.
Every record lives in this folder, one file per decision, and the log below is
their index. It holds no decisions yet, and gains a row each time a record is
written.

---

## 📝 File Log

<!-- AUTO-INDEX:BEGIN dir=. style=log fields=status,date,evidence -->

| Entry                    | Status | Date | Evidence | Purpose    |
| :----------------------- | :----- | :--- | :------- | :--------- |
| [`README.md`](README.md) | -      | -    | -        | This file. |

<!-- AUTO-INDEX:END -->

**This log is the decision index, and nobody types its rows.** The standards'
indexer draws it from each record's own frontmatter: redraw it in the same
commit as a record. **Status** is Proposed, Accepted, Superseded, or
Deprecated; **Date** is when the decision was made; **Evidence** links the
research that informed it, or reads N/A.

---

## 🌿 Adding A Decision

- [ ] Write it in this folder as `ADR-NNNN-Short-Slug.md`, taking the next
      number: its context, the options weighed, the one chosen and why, and
      the consequences.
- [ ] Set `type: record`, `status`, `date`, and `evidence` in its frontmatter.
- [ ] Redraw this log in the same commit.

A later decision supersedes an earlier one rather than rewriting it: mark the
old record **Superseded** and link the new one.

---

## 🔗 See also

- [Documentation index](../README.md) - every document this project keeps
- [Standards Index](https://github.com/tannergolden/standards/blob/Development/docs/README.md) - the canonical engineering standards

---

<div align="center">

**Write the decision down while the reasons are still fresh.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
