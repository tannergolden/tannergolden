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

**A page that writes itself, at moments nobody scheduled, from what changed this week.**

_Random by construction. Attributed by default._

</div>

---

## 💡 What Runs

One workflow, [`dispatches.yml`](.github/workflows/dispatches.yml), fires
every hour, on the hour. It reads [`state/schedule.json`](state/schedule.json),
which holds two moments: when the next dispatch is due and when the next
page refresh is due. If either falls inside the coming hour, the run sleeps
until that exact second, does the work, draws the next moment, and looks
again. When nothing is due, the run ends in seconds.

A moment already in the past, because GitHub skipped or delayed a cron, is
handled at once. The entry lands late rather than never.

The workflow can also be run by hand from the Actions tab: `tick` does what
the cron does, `dispatch` sends one dispatch now, `refresh` rewrites the page now,
and `probe` tries every source and the terminal tip once and reports what
each would have written, without writing anything. Run on any branch but the
default one, the writing modes do everything except push, and report the
commits they made in the run summary, so a change can be rehearsed before it
merges.

The dispatch badge on the page is written by the run itself, so it can go red.
A run that fails turns it red in a commit of its own, carrying nothing
fetched, and the next run that succeeds turns it back. A badge that cannot
go red is decoration.

There is no bot. The commits are made by GitHub Actions, in a workflow I wrote
and scheduled, and every one of them is authored by me.

---

## ⌨️ The Masthead

The page opens with a terminal that types itself out. `👋🏻 Hello World!` is
always first and then stays gone; twelve lines loop after it for about fifty
seconds before coming round, and a workflow draws twelve new ones every twelve
hours.

| | |
| :--- | ---: |
| Lines the generator can write | **1,000** exactly |
| Of those, narrow enough to show | 515 |
| Frames | 64, of which 42 fit the plate |
| Distinct mastheads | 1.16e+23 |
| Plate | 34 cells on one row, a 467px image |
| Hidden below | 498px, where it would have to shrink |

Nothing in it is written by hand. Each line comes from a **frame**: a sentence
shape with its own pools, small enough to have been read end to end, where
every pool is interchangeable with every other. The emoji belongs to the frame
rather than the line, so no shape can appear twice in a set without the
repetition being visible, and the test suite walks every line the generator can
produce rather than a sample.

Variety has to arrive between visits rather than during one, because GitHub
strips the script that could redraw a committed image. That is what the
twelve-hour redraw is for, and each one reads what the last committed so two
consecutive mastheads share no shape and no line returns inside four days.

> [!NOTE]
> **The full account is in [⌨️ The Masthead](Masthead.md)**: the frames, the
> arithmetic behind the combination count, the SMIL typing and the phosphor,
> the plate and what it costs, and which of five images each reader is served.
> It lives in one place so the numbers cannot drift between two.

## 🟢 Availability

One badge on this page is set by a person rather than by a source. The
[Availability workflow](.github/workflows/availability.yml) runs from the
Actions tab, offers three choices, and commits the one picked:

| Choice              | Badge reads      | Colour |
| :------------------ | :--------------- | :----- |
| 🟢 Open to role     | `Open to role`   | green  |
| 🟡 Open to consult  | `Open to consult` | yellow |
| 🔴 Not Available    | `Not Available`  | red    |

A `workflow_dispatch` choice input is single select, so this is one pick
rather than a combination. The badge is drawn by the emblems kit like every
other image here, and its URL carries a hash of its bytes, because GitHub
proxies images by URL and a status that changed would otherwise keep showing
the old colour for hours.

**Unset renders nothing.** Until somebody picks, the region is empty and no
badge appears. A profile that silently claims to be looking for work, or not
to be, is worse than one that says nothing, and nothing else in this
repository writes this line.

Running it twice with the same choice commits nothing, so the page carries no
empty commits from a second look at the dropdown.

---

## 🎲 The Randomness

The wait between dispatches is drawn from an **exponential distribution** with a
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
| Dispatches per day, on average               | Two                                     |
| Days with no dispatch at all                 | About one in seven                      |
| Gaps longer than two days                 | About six a year                        |
| Minutes between two dispatches, at the least | It has happened; it will happen again   |

A cron can only fire on a lattice, and a fixed wait after each entry is also a
lattice, just an offset one. Sleeping to the second inside an hourly run is
what turns a schedule into a moment.

The page refresh (the date line and the terminal tip) is
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
gate in [tannergolden/standards](https://github.com/tannergolden/standards),
and they hold to the whole of
[Conventional-Commits.md](https://github.com/tannergolden/standards/blob/Development/docs/distribution/Conventional-Commits.md)
rather than the part a gate can check. Two test files keep them there:
`tests/commit-message.py` carries the gate itself, ported, and
`tests/commit-standard.py` carries the rules the document states and nothing
enforces, each test naming the section it comes from.

| The standard asks for                            | Every generated commit                                                       |
| :----------------------------------------------- | :---------------------------------------------------------------------------- |
| A type from the list, and a required scope       | `docs(hn)`, `feat(trending)`, `docs(lobsters)`                              |
| A lowercase subject, imperative, under 72        | Opens with a verb: read, follow, note, surface, star, watch, track, clone    |
| One emoji from the row for that type             | Checked against the mapping table, per type                                  |
| A body on every commit, wrapped at 72            | The dispatch itself, wrapped                                                 |
| Footers after the body                           | `Source`, `Attribution`, `License`, `Signed-off-by`, in one block            |
| No dash from U+2013 to U+2015                    | Removed on ingest, before the text can reach a message                       |
| No AI trailer where no AI contributed            | A generated dispatch carries none                                            |

The footers are one block with no blank line before the sign-off, because git
parses only the last paragraph as trailers, and provenance in a paragraph of
its own would not be read as trailers at all.

**The wording varies, inside those rules.** Every dispatch of a kind used to
open with the same verb and wear the same emoji, so a screen of `git log`
read as one sentence with the nouns swapped: note, note, note, note. The content
was never repeated; the sentence around it always was.
[`src/phrasing.py`](src/phrasing.py) holds a pool of bare imperatives per
kind, the three emoji the mapping table lists for each type, and several
phrasings for the opening clause of a body. All three are drawn from the
same entropy source as the timing.

Widening a pool is the obvious way to break the standard by accident, so the
test redraws every kind eighty times and runs all seven rules over every
result. It also asserts that the emoji pools are exactly the mapping table's
rows and that every verb is a bare imperative, and that the two commits the
workflow writes about itself do **not** vary: those are status markers, and a
person greps for them.

---

## 📚 The Sources

**22 sources, in two families.** Three say what developers are
*reading*; 19 say what *happened*. A page built on either alone is worse
than one built on both: attention without news is a popularity contest, and
news without attention is a wire nobody asked for.

### The aggregators

| Commit | Content | Source |
| :--- | :--- | :--- |
| `docs(hn)` | A front-page story, its score and its conversation | Hacker News |
| `feat(trending)` | A repository the industry is starring this month | GitHub Search |
| `docs(lobsters)` | What the quiet end of the internet is reading | Lobsters |

**What counts as trending.** `docs(hn)` reads the top of the front page and
takes nothing under a hundred points, because below that a story is on its way
up or on its way out and neither is what a reader means by "what is everyone
reading". `feat(trending)` asks GitHub for repositories created inside the last
fortnight, month or quarter and already past a hundred and fifty stars: new
plus adopted, rather than famous for a decade. The window is drawn at random
each time, so the page is not three months of the same fifty repositories.

### The publishers

Three tiers, and the tier is the argument rather than a label.

**Primary.** A project publishing its own release notes. There is no
intermediary to get it wrong, so a Go release announced on the Go blog is as
close to fact as technology news gets.

| Commit | Source | Home |
| :--- | :--- | :--- |
| `feat(github)` | The GitHub Blog: Changelog | https://github.blog/changelog/ |
| `feat(python)` | Python Insider | https://pythoninsider.blogspot.com/ |
| `feat(rust)` | The Rust Blog | https://blog.rust-lang.org/ |
| `feat(golang)` | The Go Blog | https://go.dev/blog/ |
| `feat(node)` | Node.js Blog | https://nodejs.org/en/blog/ |
| `feat(kubernetes)` | Kubernetes Blog | https://kubernetes.io/blog/ |
| `feat(postgres)` | PostgreSQL News | https://www.postgresql.org/about/newsarchive/ |
| `docs(mozilla)` | Mozilla Hacks | https://hacks.mozilla.org/ |

**Registry.** A public body whose product is the record itself. Cited rather
than reported.

| Commit | Source | Home |
| :--- | :--- | :--- |
| `security(cisa)` | CISA Cybersecurity Advisories | https://www.cisa.gov/news-events/cybersecurity-advisories |

**Press.** A desk with named editors, a masthead and a corrections policy.
That is the line: a publication answers for what it prints, and a feed of
opinions does not. Each of these has been publishing technical journalism for
a decade or more, which is the only track record worth anything here.

| Commit | Source | Home |
| :--- | :--- | :--- |
| `docs(ars)` | Ars Technica | https://arstechnica.com/ |
| `docs(lwn)` | LWN.net | https://lwn.net/ |
| `docs(register)` | The Register | https://www.theregister.com/ |
| `docs(spectrum)` | IEEE Spectrum | https://spectrum.ieee.org/ |
| `docs(infoq)` | InfoQ | https://www.infoq.com/ |
| `docs(phoronix)` | Phoronix | https://www.phoronix.com/ |
| `docs(bbc)` | BBC Technology | https://www.bbc.com/news/technology |
| `docs(guardian)` | The Guardian Technology | https://www.theguardian.com/uk/technology |
| `docs(npr)` | NPR Technology | https://www.npr.org/sections/technology/ |
| `docs(verge)` | The Verge | https://www.theverge.com/ |

**One table, one fetcher.** RSS and Atom are two shapes, not nineteen.
Everything that differs between these sources is data: a URL, a name, a commit
type and a sentence about the terms. A function per source would be the same
forty lines nineteen times, and the twentieth source would be the one nobody
adds.

**A project gets longer than a newspaper.** A press desk publishes daily, so
anything from last month is stale and the standard fourteen-day window
applies. A project publishes when it ships, and a language release from three
weeks ago is still the news for anyone who has not upgraded, so primary and
registry sources get forty-five days. Holding both to fourteen would take
every primary source dark for most of the year and make that list a
decoration.

**A publisher dispatch is longer than an aggregator one**, because it has more
to say. An aggregator entry is a title and a score, and the score *is* the
story. A publisher entry arrives with the publisher's own summary, a byline
and a filing, and dropping all of that would leave a headline on the page with
nothing under it. The summary is trimmed at a sentence boundary, never
mid-word, and never past 360 characters: long enough to say what happened,
short enough that this stays a page of dispatches rather than a mirror of
somebody else's article.

**They all overlap, and that is handled.** Hacker News and Lobsters carry the
same Ars Technica piece the same morning it runs. The ledger keys on a
per-source identifier, so without more than that the page would run one
article three times under three scopes. Every dispatch therefore also claims
the canonical URL of what it sent, with tracking parameters and trailing
slashes normalised away, and a claim already taken is a story already sent.

The claim is filed when the dispatch reaches the page, not when a fetcher
finds it. A candidate the run discards must not burn the link for every other
source that carries it.

All of them are equals in the draw. If a source is down or has nothing new the
next kind is tried, and if every one comes back empty the run writes nothing
and leaves the moment in the past for the next run to catch. With
22 kinds a run almost always finds something on its first or second try.

The commit type is a genre label rather than a claim about this repository:
`feat(rust)` adds no feature here. This repository cuts no releases and runs no
changelog generator, which is the only reason that is free.

> [!IMPORTANT]
> **A feed is a document from the open internet handed to an XML parser**,
> which is the one combination here that can take the runner down rather than
> merely return nothing. Both classic attacks arrive in a document type
> declaration: an external entity that makes the parser fetch a local file,
> and nested entities that expand a kilobyte into a gigabyte. None of these
> sources needs one, so **a feed carrying a declaration is not parsed at all**.
> Refusing it outright is a complete defence against both and needs no
> dependency to implement.

---

## 🛡️ Text From The Open Internet

A story title, a repository description and a submitter's name are written by
whoever typed them, so every fetched string is treated as hostile until it has
been through [`src/text.py`](src/text.py). Comment delimiters are removed, so no
paragraph can close a page region early. Bidirectional overrides and zero-width
characters are stripped. Markdown specials are escaped rather than deleted, so
a title that looks like a link is shown as text instead of becoming one. A
mention or an issue reference in fetched text is defused, because a commit
message can notify an account or close an issue and a release note must not be
able to make this repository do either. Commit messages are written to a file
and passed to `git commit -F`, never through a shell.

Nothing fetched is reproduced as code any more. An earlier design borrowed
program listings from a wiki and had to fence them against their own backticks;
that whole path is gone, and with it the only place where untrusted text was
written into the page unescaped.

---

## ⚖️ Licensing

The code here is MIT. What the dispatches carry is fact rather than expression:
a title, a score, a star count, a domain, a link. Every one is named and linked
anyway, because attribution costs nothing and a reader should be able to check.
No dispatch source is share-alike any more; tldr-pages, which feeds the terminal
tip, is CC BY 4.0. [`NOTICE`](NOTICE) carries the terms in full.

No copyleft source is reproduced here at all. An earlier design quoted GFDL
program listings, which meant this repository had to carry the GFDL text and
a switch to turn the exposure off; both are gone.

---

## 📋 Where This Departs From The Standards

Every other repository on this account follows
[tannergolden/standards](https://github.com/tannergolden/standards) by
reference. This one departs from it in six places, listed here because an
exception nobody wrote down is a discrepancy somebody will find.

| The standard says                                                  | This repository does                                                | Why                                                                                                                                                          |
| :----------------------------------------------------------------- | :------------------------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing scheduled pushes to a protected branch; propose a pull request | The workflow pushes straight to the default branch                  | The page renders from the default branch and a pull request per random moment would be two thousand pull requests a year, reviewed by nobody                   |
| A repository holds a stub; the logic lives in `standards`          | The logic lives here, in `src/`                                     | This is a profile, not a pipeline, and its workflow is not reusable by anything else; publishing it from `standards` would bloat a library other repos consume |
| The rulesets and the standard stubs are applied                     | Neither is applied                                                  | The ruleset would refuse the push above; the stubs gate code this repository does not have. `checks.yml` runs the same lint and tests a contributor runs      |
| A commit's type carries the intent of the change                   | The type is a genre label for the content                           | Stated above. The exception holds only while this repository cuts no releases and runs no changelog tooling                                                   |
| A body explains why the change was made, and why this way          | A dispatch body carries the dispatch                                | The why would be the same sentence on every commit of a kind, which is the restatement the standard itself warns against. The footers carry what a reader cannot recover: source, licence, attribution |

Everything else holds: the commit gate, the body on every commit, the
sign-off, the frontmatter, the header and footer, the em dash ban in every
file, the pinned actions, the hardened runner, the least-privilege token.

---

## ✏️ Where The Words Come From

Nothing generated is written by hand, and nothing written by hand is
generated. The hand-written parts live in three places:

| File                       | What it holds                                                          |
| :------------------------- | :--------------------------------------------------------------------- |
| `README.md`                | Everything outside the six marked regions                              |
| [`.github/badges.yml`](.github/badges.yml) | Every badge, the stack included; `make badges` renders them             |

The archive keeps its own index, [`dispatches/README.md`](dispatches/README.md),
with a month table the run regenerates between markers each time it writes.

---

## 🔗 See Also

- [⌨️ The Masthead](Masthead.md), the terminal at the top of the page in full.
- The [archive](dispatches/), one file per month, appended and never rewritten.
- [`NOTICE`](NOTICE), the source and license terms in full.
- [tannergolden/emblems](https://github.com/tannergolden/emblems), which draws every badge on the page as a committed file, so the page makes no request to an image service.

---

<div align="center">

**Scheduled by nothing. Signed by someone.**

[↑ Back to Top](#top)

</div>
