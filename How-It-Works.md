<!--
title: '🕒 HOW IT WORKS'
description: 'How this profile writes itself: the randomness, the sources, the authorship, the licensing, and the places it deliberately departs from the standards the rest of the account follows.'
tags: [automation, github-actions, randomness, provenance]
category: docs
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# 🕒 HOW IT WORKS

<a name="top"></a>

**A page that writes itself, at moments nobody scheduled, from sources that never run dry.**

_Random by construction. Attributed by default._

</div>

---

## 💡 What Runs

One workflow, [`journal.yml`](.github/workflows/journal.yml), fires every hour at
seventeen minutes past. It reads [`state/schedule.json`](state/schedule.json),
which holds two moments: when the next journal entry is due and when the next
page refresh is due. If either falls inside the coming hour, the run sleeps
until that exact second, does the work, draws the next moment, and looks
again. When nothing is due, the run ends in seconds.

A moment already in the past, because GitHub skipped or delayed a cron, is
handled at once. The entry lands late rather than never.

The workflow can also be run by hand from the Actions tab: `tick` does what
the cron does, `entry` writes one entry now, `refresh` rewrites the page now,
and `probe` tries every source and every module once and reports what each
would have written, without writing anything. Run on any branch but the
default one, the writing modes do everything except push, and report the
commits they made in the run summary, so a change can be rehearsed before it
merges.

The journal badge on the page is written by the run itself, so it can go red.
A run that fails turns it red in a commit of its own, carrying nothing
fetched, and the next run that succeeds turns it back. A badge that cannot
go red is decoration.

There is no bot. The commits are made by GitHub Actions, in a workflow I wrote
and scheduled, and every one of them is authored by me.

---

## 🎲 The Randomness

The wait between entries is drawn from an **exponential distribution** with a
mean of twelve hours, set once in [`src/config.py`](src/config.py). That is the
waiting time of a Poisson process, and it is the only distribution with the
property being bought here: it is memoryless. Knowing when the last entry
landed tells you nothing about when the next one will.

The draw comes from the operating system's entropy source, through Python's
`random.SystemRandom`, the same source `secrets` reads. Nothing is seeded,
because a seeded sequence is reproducible and reproducible is the opposite of
random.

What twelve hours means in practice:

| Question                                  | Answer                                  |
| :---------------------------------------- | :-------------------------------------- |
| Entries per day, on average               | Two                                     |
| Days with no entry at all                 | About one in seven                      |
| Gaps longer than two days                 | About six a year                        |
| Minutes between two entries, at the least | It has happened; it will happen again   |

A cron can only fire on a lattice, and a fixed wait after each entry is also a
lattice, just an offset one. Sleeping to the second inside an hourly run is
what turns a schedule into a moment.

The page refresh (the date line, the three daily modules, the two cards) is
drawn the same way, with a mean of one day, so it also lands at an
unremarkable hour.

---

## 🔒 One Writer

A run that is asleep holds the workflow's concurrency group. The next hourly
run queues behind it rather than committing beside it, and a sleeping run is
never cancelled, because cancelling it would lose the moment it was waiting
for. Before every push the run rebases onto whatever landed meanwhile, so a
change I make by hand is never overwritten.

---

## ✍️ Who The Commit Is By

Every generated commit is **authored by me**, with my GitHub noreply address,
and **committed by `github-actions[bot]`**. The contribution graph reads the
author, so these count as mine, which is deliberate: I built and scheduled
the generator, and I am the one accountable for what it writes. The committer
field records that a machine performed the write, so the object is honest
about both.

Because the author is a person, these commits are not exempt from the commit
gate in [tannergolden/standards](https://github.com/tannergolden/standards):
scope required, lowercase subject after an optional emoji, no dash from
U+2013 to U+2015 anywhere in the message, a body on every commit, a subject
under 72 characters. The test suite proves every generated message passes it.

---

## 📚 The Sources

Every kind draws on a corpus that is either enormous or still growing. That is
what lets the ledger in [`state/ledger.json`](state/ledger.json) promise that
no item appears twice: the identifier of everything ever used is recorded, and
the promise costs nothing while the well is deeper than the lifetime of the
page.

| Commit                | Content                                                 | Source                     | License                     |
| :-------------------- | :------------------------------------------------------ | :------------------------- | :-------------------------- |
| `chore(release)`      | Software and games released on this date                | Wikidata                   | CC0 1.0                     |
| `docs(born)`          | Computing people born on this date                      | Wikidata                   | CC0 1.0                     |
| `refactor(rosetta)`   | One task, one language, the code                        | Rosetta Code               | GFDL 1.2, this version only |
| `feat(unicode)`       | A character with a name worth reading                   | Unicode Character Database | Unicode License v3          |
| `docs(rfc)`           | An RFC, what it did, and when                           | RFC Editor                 | Freely reproducible         |
| `docs(xkcd)`          | A comic, its title and hover text, by number            | xkcd                       | CC BY-NC 2.5                |
| `test(sequence)`      | Eight terms, and the ninth in the body                  | OEIS                       | CC BY-SA 4.0                |
| `fix(bug)`, rare      | A famous software failure                               | Wikipedia                  | CC BY-SA 4.0                |
| `fix(falsehood)`, rare | A catalogue of things programmers believe               | awesome-falsehood          | CC0 1.0 (the list)          |

The two rare kinds together take one draw in twenty, and each retires when its
list is used up. `docs(born)` is offered only on a date somebody qualifying was
born; otherwise another kind is drawn. If a source is down or empty, the next
kind is tried, and if every source fails the run writes nothing and leaves the
moment in the past for the next run to catch.

The commit type is a genre label: `feat(unicode)` adds nothing to any
software, and `fix(bug)` fixes nothing. This repository cuts no releases and
runs no changelog generator, which is the only reason that joke is free.

---

## 🛡️ Text From The Open Internet

Four of the nine sources are wikis anyone can edit, and every fetched string
is treated as hostile until it has been through [`src/text.py`](src/text.py).
Comment delimiters are removed, so no paragraph can close a page region early.
A borrowed snippet is fenced with more backticks than it contains, so it
cannot end its own block. Bidirectional overrides and zero-width characters
are stripped. A language name is cut down to what a language name can be
before it follows a fence, since a backtick there would stop the fence
from opening. A mention or an issue reference in fetched text is defused,
because a commit message can notify an account or close an issue and a
wiki edit must not be able to make this repository do either. Commit
messages are written to a file and passed to `git commit -F`, never
through a shell.

---

## ⚖️ Licensing

The code here is MIT. The journal reproduces or derives from the sources above,
each entry names its source and license, and [`NOTICE`](NOTICE) carries the
terms in full. Two sources are share-alike and one is GFDL; those entries are
available under those licenses, marked individually, and nothing else in the
repository is affected by them. Rosetta Code snippets are capped at fifteen
lines and cite the exact wiki revision they came from. Setting
`JOURNAL_ROSETTA_CODE=0` makes that kind cite without reproducing, which
removes the GFDL exposure entirely.

---

## 📋 Where This Departs From The Standards

Every other repository on this account follows
[tannergolden/standards](https://github.com/tannergolden/standards) by
reference. This one departs from it in five places, listed here because an
exception nobody wrote down is a discrepancy somebody will find.

| The standard says                                                  | This repository does                                                | Why                                                                                                                                                          |
| :----------------------------------------------------------------- | :------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing scheduled pushes to a protected branch; propose a pull request | The workflow pushes straight to the default branch                  | The page renders from the default branch and a pull request per random moment would be two thousand pull requests a year, reviewed by nobody                   |
| Every cron fires at minute 00                                      | This one fires at :17                                               | The on-the-hour rule staggers many jobs sharing one API; this repository has one job, and GitHub's scheduler delays or drops runs most often on the hour       |
| A repository holds a stub; the logic lives in `standards`          | The logic lives here, in `src/`                                     | This is a profile, not a pipeline, and its workflow is not reusable by anything else; publishing it from `standards` would bloat a library other repos consume |
| The rulesets and the standard stubs are applied                     | Neither is applied                                                  | The ruleset would refuse the push above; the stubs gate code this repository does not have. `checks.yml` runs the same lint and tests a contributor runs      |
| A commit's type carries the intent of the change                   | The type is a genre label for the content                           | Stated above. The exception holds only while this repository cuts no releases and runs no changelog tooling                                                   |

Everything else holds: the commit gate, the body on every commit, the
sign-off, the frontmatter, the header and footer, the em dash ban in every
file, the pinned actions, the hardened runner, the least-privilege token.

---

## ✏️ Where The Words Come From

Nothing generated is written by hand, and nothing written by hand is
generated. The hand-written parts live in three places:

| File                       | What it holds                                                          |
| :------------------------- | :--------------------------------------------------------------------- |
| `README.md`                | Everything outside the five marked regions                             |
| [`profile.json`](profile.json) | The phrases the typing header cycles through, and the languages the good-first-issue search covers |
| [`.github/badges.yml`](.github/badges.yml) | Every badge, the stack included; `make badges` renders them             |

The journal archive keeps its own index, [`journal/README.md`](journal/README.md),
with a month table the run regenerates between markers each time it writes.

---

## 🔗 See Also

- The [journal](journal/), one file per month, appended and never rewritten.
- [`NOTICE`](NOTICE), the source and license terms in full.
- [tannergolden/emblems](https://github.com/tannergolden/emblems), which draws every badge on the page as a committed file, so the page makes no request to an image service.

---

<div align="center">

**Scheduled by nothing. Signed by someone.**

[↑ Back to Top](#top)

</div>
