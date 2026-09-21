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

One workflow, [`dispatches.yml`](.github/workflows/dispatches.yml), fires every hour at
seventeen minutes past. It reads [`state/schedule.json`](state/schedule.json),
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
always first; the twelve lines after it are assembled from
[`src/masthead.py`](src/masthead.py) and drawn into SVG by
[`src/cards.py`](src/cards.py).

Not from a word salad. A slot filled at random from a pool that fits every
other slot in its frame produces grammar by accident and nonsense by default,
and an earlier draft of this really did offer "Automating more than I add" and
"Deleting what people forget". Each frame now carries its own pools, small
enough to have been read end to end, and the test walks **every** line the
generator can produce rather than a sample: a generator nobody can enumerate
is a generator nobody can vouch for.

| | |
| :--- | ---: |
| Lines, the greeting included | **1,000** exactly |
| Frames | 64 |
| Distinct mastheads (twelve drawn from sixty-four frames) | 6.77 x 10^26 |
| Words per line | 4 to 8 |
| Widest line | 49 cells, wrapped onto at most 2 rows of 26 |
| Image | at most 407 x 84, which fits a phone column unscaled |
| Typing | 20 cells a second, constant |
| Greeting | 2.8 seconds, once |
| Loop | about 55 seconds, forever |
| Redrawn | every 12 hours, and it remembers the last 4 days |

A thousand is a promise rather than an accident: the pools are sized to land
on it, and a test fails the day one of them drifts.

**Why twelve lines.** Dwell time on a web page follows a Weibull distribution
with negative aging, per Nielsen Norman's reading of Liu, White and Dumais:
the first ten seconds decide it, the next twenty thin the survivors, and only
past about thirty seconds does the curve flatten. Cross-industry average time
on a page is 52 to 54 seconds. Twelve lines is a 56-second loop, which
outlasts that average. Past twenty the loop only serves a flat tail that no
finite animation can serve anyway, at real CPU in every open tab.

**Sixty-four frames, by what they are for.** One emoji each, so no shape can
appear twice in a set.

| | Frames |
| :--- | :--- |
| What the work is | 🔒 🚀 🕒 🔐 ⛓️ |
| What it is for | ♻️ 📖 🧪 💤 🧾 |
| Preferences, stated as preferences | 🧭 🧰 🎯 🏗️ 📋 |
| Where the effort goes | 🧹 ✂️ 📦 📉 🚮 |
| The supply chain | 📌 🔗 🏷️ 🧊 🗓️ |
| Reproducibility | ⚙️ 🔁 🗺️ 🧬 🔭 |
| Operating it | 🧯 🔔 🛟 🩺 🪫 |
| What you can see | 🔍 🪵 🧮 💡 📊 |
| Secrets | 🗝️ 🎚️ |
| Shape and review | 🪞 📐 💬 🧩 🗃️ |
| Decay, and refusing it | 🌱 🚧 ⏳ 🔋 🪄 |
| Research that holds up | 🔬 🎛️ 🛠️ |
| Delivery | 📮 ⏱️ 🚦 |
| The next person | 🎓 📝 🌐 🧱 |
| The page talking about itself | 🎲 🤖 |

**Why frames rather than bigger pools.** Twelve lines drawn from fifteen
frames put every masthead at eighty per cent of all the shapes there were, so
two consecutive draws shared ten of their twelve emoji and the page read as
repetitive however much the words changed. Sixty-four puts a draw at nineteen
per cent, and two consecutive ones share about two.

The line count is the same thousand either way, and frame count is close to
free for how often a line comes back: for evenly sized frames the expected
wait is 999/12 draws whatever the frame count, because a rarer frame holds
correspondingly fewer lines. What more frames buy is the part a reader
actually notices, which is the shapes.

**Redrawn every twelve hours**, by
[a workflow of its own](.github/workflows/masthead.yml), and its commit
message is drawn the same way the lines are: 8,736 of them, because a log
carrying the same paragraph twice a day is a log nobody reads twice. Every
frame it can draw from states a why, since the commit standard asks for one
and a generated body is the easiest place in a repository to restate a
subject instead. Every other schedule
here is an exponential draw, because a dispatch arriving on the hour is one
nobody believes is random. The masthead is not news and nothing about it is
due at a moment, so it is the honest exception: a clock, at 06:41 and 18:41
UTC, off the hour for the same congestion reason the dispatch cron is.

**It wraps, and that is the single thing that makes it readable on a phone.**
GitHub scales a README image down to the column, and the column on a phone is
about 330 pixels. A forty nine cell line on one row is a 570 pixel image,
which arrives at 0.6 scale and an effective font of **ten pixels**: a green
smear rather than a masthead. Every line is wrapped onto at most two rows of
twenty six cells, which holds the image at 407 pixels at its widest and needs
almost no scaling at all.

Twenty six is not a round number. It is the last cap where every one of the
thousand lines still fits two rows; at twenty four, twelve of them spill onto
a third. The split is balanced rather than greedy, because greedy fills the
first row and leaves the second holding two words, which reads as a mistake.

Wrapping also paid for a bigger font. Once a row fits the column, the font and
the image grow together and the effective size on a phone barely moves, so the
type went from 18 to 22 and the desktop reader is the only one who notices.

| | one row, 18px | wrapped, 22px |
| :--- | ---: | ---: |
| Image | 570 x 56 | 407 x 84 |
| Effective font on a 328px column | 10.4px | 17.7px |

**The greeting types once and does not come back.** It runs on a timeline of
its own with `repeatCount="1"`, and the drawn lines loop among themselves on a
second one that begins where the first finished erasing. A greeting that
greets the same reader again every minute is a tic rather than a welcome,
which is what the first version did.

**Reloading the page will not change the lines.** GitHub serves a committed
file and strips the script that could redraw one, which is the same constraint
that makes the animation SMIL. The lines change when a run writes them, so
they are redrawn on every dispatch as well as on every page refresh: a few
times a day rather than once.

The count that matters is the second one. A reader takes in the set at once,
so two mastheads differing in one line are two different mastheads.

**The background is transparent**, so the text sits on whatever colour GitHub
is painting behind it, and that is white on one theme and near-black on the
other. No single green clears the contrast bar on both: neon `#00ff41` is
13.9:1 on GitHub's dark and **1.4:1 on white**, which is invisible. So there
are two files and a `<picture>`, the same answer the cards reach for. Dark
gets the neon and the bloom; light gets `#067d17` at 5.3:1 and no bloom,
because a glow around dark green on white is a smudge.

The reveal steps one cell at a time rather than growing smoothly, because a
rectangle widening continuously uncovers letters through their own middles and
reads as a wipe. Stepping by whole cells is what makes it look typed.

**One cadence, not one duration.** The first version gave every line the same
1.6 seconds whatever its length, so a seventeen cell greeting crawled and a
forty nine cell line blurred past at three times the speed. Typing is now a
constant twenty cells a second and the pause afterwards is reading time,
0.95 seconds plus 0.04 a cell, so a long line is held about twice as long as a
short one. The loop varies with what was drawn, between roughly fifty and
sixty seconds.

The keystrokes themselves are not evenly spaced: there is a beat before a new
word and a longer one after a full stop, and no two are the same length. The
variation is seeded from the line's own text rather than from chance, so the
same line always types the same way and a run that redrew nothing produces a
file that changed nothing. An emoji is two cells wide and one keystroke, so
its second cell arrives in no time at all and the clip never rests through the
middle of a glyph showing half a face.

**The cursor is solid while it types**, the way a real one is, and blinks only
while a finished line sits waiting to be read. It follows the text down onto
the second row when a line wraps. There is one cursor per line rather than one
per row, and only ever one lit at a time.

**Three ways to read it.** A browser types it out. A renderer with no SMIL at
all shows the greeting complete, because the greeting's clip rectangles carry
their full width as a plain attribute and an animation is what overrides that
rather than what supplies it; `fill="freeze"` is what stops the animation
handing that width back at the end of its one run. A reader who has asked for
less motion gets the same still line, from a layer a `prefers-reduced-motion`
query swaps in: text that types itself is exactly the motion that setting is
about.

**The glow is two passes, not one.** A single blur merged with itself is a
smudge with a bright middle. A phosphor has a hard centre and soft light well
beyond it, so there is a tight core at 0.045em and a wide halo at 0.2em with
its alpha cut to 55%. `color-interpolation-filters="sRGB"` is on the filter
because the default is linearRGB, which turns a saturated green bloom into a
pale grey one.

**Each redraw remembers the last one.** Random with no memory repeats far
sooner than anybody expects: twelve of sixty-four shapes, drawn twice a day,
put a shape from yesterday back on the page more often than not. A redraw
reads what the last one committed and excludes its frames, so two consecutive
mastheads share no shape at all, and excludes the lines of the last eight
draws, which is four days. Both fall back to the full set rather than fail,
because a masthead with a hole in it is worse than a repeat. The memory lives
in `assets/masthead.json` beside the images rather than in the state
directory, so the image and the record of how it was drawn are always in the
same commit and can never disagree.

The rectangle is anchored at the left edge of the image while the text starts
16px inside it, so every width it steps through carries that inset. The first
version did not, and the longest line stopped one and a half characters short
of finishing: `Standards that a new machine cannot brea`.

**No script, anywhere.** GitHub strips those from an SVG in a README, which is
why the animation is SMIL and the words are chosen in Python. The glow is an
SVG filter, and a filter is the one thing here whose survival through GitHub's
sanitiser is unproven; it degrades to flat green on black, which is the same
picture without the bloom.

---

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

The page refresh (the date line, the terminal tip, the two cards) is
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

Three sources, chosen for one property: they say what developers are actually
reading and starring this week, rather than what was published this week. An
earlier design drew on primary records instead, a release cut, an advisory
reviewed, a standard published, and it was authoritative and almost never
about anything anybody was talking about.

| Commit            | Content                                           | Source           | License                       |
| :---------------- | :-------------------------------------------------- | :--------------- | :---------------------------- |
| `docs(hn)`        | A front-page story, its score and its conversation  | Hacker News      | Title, score and link, as fact |
| `feat(trending)`  | A repository the industry is starring this month    | GitHub Search    | Metadata, reported as fact    |
| `docs(lobsters)`  | What the quiet end of the internet is reading       | Lobsters         | Title and score, as fact      |

**All three lists are current by construction.** A front page, a hottest list
and a search for repositories created this month cannot return last year, so
freshness is a property of the source rather than something this has to
enforce. Lobsters still carries a window on the story's own date,
`DISPATCH_NEWS_WINDOW_DAYS`, as a guard against an outlier. An item whose date
will not parse is not treated as an old one: the two are different answers, and
collapsing them would take a whole kind dark the day a source renames a field.

**The three overlap, and that is handled.** Hacker News and Lobsters carry the
same link on the same morning more often than not, and a trending repository is
frequently the thing both are discussing. The ledger keys on a per-source
identifier, so without more than that the page would run one article three
times under three scopes. Every dispatch therefore also claims the canonical
URL of what it sent, with tracking parameters and trailing slashes normalised
away, and a claim already taken is a story already sent.

The claim is filed when the dispatch reaches the page, not when a fetcher finds
it. A candidate the run discards must not burn the link for the other two
sources that carry it.

The three are equals in the draw. If a source is down or has nothing new the
next kind is tried, and if all three come back empty the run writes nothing and
leaves the moment in the past for the next run to catch.

The commit type is a genre label rather than a claim about this repository:
`feat(trending)` adds no feature here. This repository cuts no releases and
runs no changelog generator, which is the only reason that is free.

**What counts as trending.** `docs(hn)` reads the top of the front page and
takes nothing under a hundred points, because below that a story is on its way
up or on its way out and neither is what a reader means by "what is everyone
reading". `feat(trending)` asks GitHub for repositories created inside the last
fortnight, month or quarter and already past a hundred and fifty stars: new
plus adopted, rather than famous for a decade. The window is drawn at random
each time, so the page is not three months of the same fifty repositories.

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
| Every cron fires at minute 00                                      | This one fires at :17                                               | The on-the-hour rule staggers many jobs sharing one API; this repository has one job, and GitHub's scheduler delays or drops runs most often on the hour       |
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

- The [archive](dispatches/), one file per month, appended and never rewritten.
- [`NOTICE`](NOTICE), the source and license terms in full.
- [tannergolden/emblems](https://github.com/tannergolden/emblems), which draws every badge on the page as a committed file, so the page makes no request to an image service.

---

<div align="center">

**Scheduled by nothing. Signed by someone.**

[↑ Back to Top](#top)

</div>
