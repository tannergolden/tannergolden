<!--
title: '⌨️ THE MASTHEAD'
description: 'How the terminal at the top of this page writes itself, and everything it can say.'
tags: [masthead, svg-animation, generative-text, accessibility]
category: docs
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# ⌨️ THE MASTHEAD

<a name="top"></a>

**How the terminal at the top of this page writes itself, and everything it can say.**

_Drawn, not written. Counted, not guessed._

</div>

---

## 💡 What It Is

The page opens with a terminal typing itself out. `👋🏻 Hello World!` comes
first and then stays gone, and twelve lines loop after it for about fifty
seconds before coming round.

Nothing about those twelve was written by hand. They are assembled at redraw
time from [`src/masthead.py`](src/masthead.py) and drawn into SVG by
[`src/cards.py`](src/cards.py), committed as files, and served by GitHub like
any other image on the page.

| | |
| :--- | ---: |
| Lines the generator can write | **1,000** exactly, the greeting included |
| Of those, narrow enough to show | 515 |
| Frames | 64, of which 42 fit the plate |
| **Distinct mastheads** | **1.16 x 10<sup>23</sup>** |
| Distinct commit messages | 8,736 |
| Lines on screen at once | 1, drawn from 12 per redraw |
| Loop | about 51 seconds |
| Redrawn | every 12 hours |

---

## 🧠 Why It Exists At All

Everything else on this page reports something: what changed this week, what
the account is made of, whether its owner is available. The masthead reports
nothing. It is the one part of the page that exists to be read rather than to
inform, which makes it the one part whose only job is to be worth a second
visit.

That job is harder than it sounds, because **nothing in a README can respond
to the reader.** GitHub strips `<script>` from an SVG in a README, so the
image cannot know it has been seen before, cannot reshuffle on reload, and
cannot react to anything. A reader who stays long enough watches the loop come
round, and reloading changes nothing, because the file they are served is the
file that was committed.

So variety has to arrive **between visits** rather than during one. That is
what the twelve-hour redraw is for, and it is why the interesting number is
not how many lines exist but how many distinct *sets of twelve* do.

> [!NOTE]
> This is also why the masthead is the one thing here on a fixed clock. Every
> other schedule in this repository is an exponential draw, because a dispatch
> arriving on the hour is one nobody believes is random. The masthead is not
> news and nothing about it is due at a moment, so a clock is the honest
> design rather than a lazy one.

---

## ✍️ How A Line Is Made

Not from a word salad. A slot filled at random from a pool that fits every
other slot in its frame produces grammar by accident and nonsense by default.
An earlier draft of this really did offer "Automating more than I add" and
"Deleting what people forget".

Each **frame** instead carries its own pools, small enough to have been read
end to end:

```python
Frame("\U0001F680", "{} {} {}", (
    ("Shipping", "Releasing", "Deploying"),
    ("a change", "a fix", "a version"),
    ("behind a gate", "with a rollback ready"),
))
```

Every pool in a frame is interchangeable with every other, which is what makes
the product of their lengths a count of **sentences** rather than a count of
strings. That frame writes eighteen of them, and every one is something a
person would say.

Three rules hold the quality up:

- **The emoji belongs to the frame, not to the line.** An emoji drawn
  independently of the words lands on the wrong ones about as often as the
  right ones. One emoji per frame also means no shape can appear twice in a
  set without the repetition being visible.
- **Every line is checked, not sampled.** The test suite walks `every_line()`
  end to end rather than spot-checking: word count, cell width, capitalisation,
  banned punctuation, and the characters that could break out of an SVG. A
  generator nobody can enumerate is a generator nobody can vouch for.
- **A frame must earn its place.** Fewer than four combinations and it is a
  sentence wearing a costume; pools with duplicates are rejected outright.

---

## 🔢 How Many Combinations

A masthead is **twelve frames drawn without replacement, then one line drawn
from each**. So the count is the sum, over every twelve-frame subset, of the
product of those frames' line counts:

```text
N  =  sum over every 12-frame subset S  of  ( product of n_f for f in S )
```

That is the elementary symmetric polynomial of degree 12 over the per-frame
counts, which a dynamic program evaluates in a few dozen steps. Enumerating
the subsets instead would mean walking C(42, 12) = 1.1 x 10<sup>10</sup> of
them, so the identity is worth checking rather than trusting: a test verifies the recurrence
against brute force on a small case where brute force is possible.

### The Answer

There are **115,895,023,955,407,099,204,396** distinct mastheads, or
**1.16 x 10<sup>23</sup>**.

At two redraws a day, exhausting them takes about 1.6 x 10<sup>20</sup> years,
which is roughly eleven billion times the age of the universe. The set you are
looking at has, to any standard that matters, never been shown before and will
never be shown again.

### What Repeats, And When

The set never repeats. Individual lines do, and how often they come back is
the number worth knowing:

| | At two redraws a day |
| :--- | ---: |
| The same twelve-line set | never, in any practical sense |
| One specific line, commonest case | median 9.5 days |
| One specific line, typical case | median 14 days |
| One specific line, rarest case | median 19 days |
| **Any** previously seen line, without memory | about 1 day |
| **Any** previously seen line, with memory | **4 days, guaranteed** |

That last row is not a statistic; it is a rule. Each redraw reads what the last
one committed and excludes it:

- **The shapes the last draw used**, so two consecutive mastheads share no
  frame at all. Twelve of forty-two shapes twice a day would otherwise put a
  shape from yesterday back on the page more often than not.
- **The lines of the last eight draws**, which is ninety-six lines and four
  days.

Both fall back to the full set rather than fail, because a masthead with a hole
in it is worse than a line somebody has seen before. The memory lives in
`assets/masthead.json` beside the images rather than in the state directory, so
the image and the record of how it was drawn are always in one commit and can
never disagree.

### Why Frames Rather Than Bigger Pools

Twelve lines drawn from fifteen frames put every masthead at eighty per cent of
all the shapes there were, so two consecutive draws shared ten of their twelve
emoji and the page read as repetitive however much the words changed.
Sixty-four written frames, of which forty-two survive the plate, put a draw at
twenty-nine per cent, and the shape memory takes the overlap between two
consecutive draws to zero.

The line count is nearly the same either way, and frame count barely changes
how often a line comes back, because a rarer frame holds correspondingly fewer
lines. What more frames buy is the part a reader actually notices: the shapes.

---

## 🎞️ How It Is Drawn

No script, so the animation is **SMIL** and the words are chosen in Python
rather than in the image.

Each line is a `<text>` element with its own `<clipPath>`, and the clip
rectangle's width steps one cell at a time with `calcMode="discrete"`. A
rectangle whose width grows continuously uncovers letters through their own
middles and reads as a wipe; stepping by whole cells is what makes it look
typed.

### Timing

| Phase | Rate | Why |
| :--- | :--- | :--- |
| Typing | 20 cells a second, constant | A terminal has one cadence. A fixed duration per line made a short line crawl and a long one blur past at three times the speed |
| Hold | 0.95s + 0.04s a cell | Reading time. Two hundred words a minute puts a six-word line at about 1.8 seconds, so a longer line earns a longer pause |
| Erase | 56 cells a second | A wipe, not a performance |
| Blink | 0.5s | Only while a finished line waits |

The keystrokes are not evenly spaced. There is a beat before a new word and a
longer one after a full stop, and no two are the same length. The variation is
**seeded from the line's own text** rather than from chance, so the same line
always types the same way and a run that redrew nothing produces a
byte-identical file. An emoji is two cells wide and one keystroke, so its second
cell arrives in no time at all, and the clip never comes to rest in the middle
of a glyph, showing half a face.

The cursor is **solid while it types**, the way a real one is, and blinks only
while a finished line waits to be read. There is one cursor per line, never two
lit at once.

### Colour And Light

The background is transparent, so the text sits on whatever GitHub paints
behind it, and that is white on one theme and near-black on the other. **No
single green clears the contrast bar on both:**

| Scheme | Ink | On its own background | On the other |
| :--- | :--- | ---: | ---: |
| Dark | `#00ff41` | 13.9:1 | 1.4:1, invisible |
| Light | `#067d17` | 5.3:1 | dim and muddy |

So there are two files and a `<picture>`. Dark gets the neon and the bloom;
light gets no bloom at all, because a glow around dark green on white is a
smudge.

The bloom is two passes, not one. A single blur merged with itself is a blurry
copy of the text: it thickens every stroke and softens every edge. What a
phosphor actually looks like is a hard glyph sitting in light, so both blurs
are **dimmed and laid behind an untouched `SourceGraphic`**. The filter also
carries `color-interpolation-filters="sRGB"`, because the default is linearRGB,
which turns a saturated green bloom into a pale grey one.

> [!IMPORTANT]
> This was not a refinement. With the glow laid over the glyphs the masthead
> read as a green smear on a phone, and fixing the light did more for
> legibility than any change to the layout.

---

## 📐 The Plate, And What A Phone Gets

**GitHub scales a README image down to its column**, and the column on a phone
is about 330 CSS pixels. The effective font size is that column divided by the
cells, and **the font size set in the renderer cancels out of it entirely**: a
bigger font widens the image by exactly the proportion GitHub then scales back
down. Cells are the only lever there is.

| Longest line shown | Image | On a 328px column |
| :--- | ---: | ---: |
| 49 cells (unconstrained) | 649px | 10.1px |
| **34 cells (the plate)** | **467px** | **14.0px** |

So the masthead draws only from lines that fit **34 cells**, and only from
frames that keep at least **eight** of them. Eight, because a frame appears at
most seven times inside the memory window (the last draw's shapes being
excluded from the next), so eight is what makes "no line twice in four days"
true rather than hoped for. Without that floor, the plate leaves one frame
holding a single line, which would then be the only thing that frame ever said.

> [!WARNING]
> **This costs 484 lines, and it is not hidden.** The generator still writes a
> thousand; 515 of them fit, across 42 of the 64 frames. `drawable()` counts
> what can be shown and `combinations()` counts what exists, both pinned by a
> test, so the shortfall cannot drift quietly. Getting all thousand back under
> the plate means rewriting fifty-one frames so their lines
> run to four or six words, which is a separate job.

Wrapping onto two rows was tried and taken back out. It put a phone at eighteen
pixels, but a masthead that breaks mid-sentence reads as a mistake on every
screen, and that cost falls on every reader rather than only on the ones
holding a phone. The renderer still wraps if `WRAP_CELLS` is lowered, and a
test keeps that path exercised so it cannot rot.

### Below 498 Pixels It Is Not Shown At All

That is the width where the plate stops fitting the column, derived from the
plate rather than typed in, so it cannot be left behind the next time the plate
moves. Below it, everything is an image being scaled down. A phone gets one
transparent pixel instead and the badges move up to take the space.

---

## 🖼️ Which Reader Gets Which Image

Five files, one `<picture>`, and **the order of the sources is the whole
thing**: a browser takes the first one whose media matches, so the narrower
conditions come first.

```html
<picture>
  <source media="(max-width: 498px)" srcset="assets/masthead-blank.svg">
  <source media="(prefers-reduced-motion: reduce) and (prefers-color-scheme: dark)"
          srcset="assets/masthead-still-dark.svg">
  <source media="(prefers-reduced-motion: reduce)" srcset="assets/masthead-still-light.svg">
  <source media="(prefers-color-scheme: dark)" srcset="assets/masthead-dark.svg">
  <img alt="every line it types" src="assets/masthead-light.svg">
</picture>
```

| Reader | Gets | Size |
| :--- | :--- | ---: |
| Phone, any theme | one transparent pixel | 125 B |
| Reduced motion, dark | a still transcript | 1.9 KB |
| Reduced motion, light | a still transcript | 1.3 KB |
| Dark theme | the animation | 37 KB |
| Anything else | the animation, light | 36 KB |

> [!TIP]
> **All of this rests on GitHub keeping `media` on a `<source>` whatever the
> query says**, and GitHub documents `prefers-color-scheme` and nothing else.
> It was checked rather than assumed: a probe file carrying
> `media="(max-width: 500px)"` was pushed to a branch and its rendered page
> fetched back, and the attribute came through the renderer intact.

### Three Ways To Fail Gracefully

- **No SMIL.** Every clip starts at width zero, so a renderer that ignores the
  animations would show an empty box. The greeting's clip therefore carries its
  full width as a plain attribute, which an animation **overrides** rather than
  supplies, and `fill="freeze"` stops it handing that width back at the end of
  its one run. Such a renderer shows a finished greeting.
- **Reduced motion.** Text that types itself is exactly the motion that setting
  is about, so those readers get a static transcript of the first four lines,
  each with its own prompt, the way a terminal shows what has already been
  typed. Reduced motion costs the movement, not the content.
- **No images at all.** The alt text lives on the `<img>`, which is where a
  screen reader reads it from **whichever source the browser picked**, so a
  phone still announces every line it would have typed. Hiding the masthead is
  a visual decision and is not allowed to become an accessibility one.

> [!NOTE]
> The reduced-motion switch cannot live inside the SVG. A preference media
> query in an image's own stylesheet never matches when that image is loaded as
> an `<img>`, because the preference does not reach the isolated image
> document. It was written that way first, a review called it doubtful, and a
> real browser settled it: the query never fired. Dimension queries like
> `max-width` do fire, which is why the breakpoint works and the motion switch
> had to move out to the `<picture>`.

---

## 🔁 How It Is Redrawn

[`.github/workflows/masthead.yml`](.github/workflows/masthead.yml) runs at
06:41 and 18:41 UTC, off the hour because GitHub's scheduler is most congested
on it, and runs there are delayed or dropped most often. It shares a concurrency
group with the other writing workflows, so no redraw lands beside a dispatch.

The commit message is **drawn the same way the lines are**, from 8,736
combinations: a subject, a reason a redraw exists at all, and a reason it is on
a clock. A log carrying the same paragraph twice a day is a log nobody reads
twice. Every frame the body can draw from states a *why*, because the commit standard
asks for one and a generated body is the easiest place in a repository to
restate a subject instead.

Images are cache-busted with eight hex characters of their own content hash.
GitHub's image proxy caches by URL, so a file rewritten at a stable path can
keep serving its previous contents for hours; a tag derived from the bytes
changes exactly when the image does and never otherwise.

---

## 🧾 Departures Worth Knowing

- **484 of the 999 generated lines are currently undrawable.** They are
  written, tested and counted; the plate is narrower than they are. See the
  plate section above.
- **A fixed schedule**, where everything else here is an exponential draw.
- **The corpus is finite and small enough to read.** That is deliberate. The
  space is not infinite; it is deeper than the number of times this page will
  ever be looked at, which is the property actually being bought.

---

## 🔗 See Also

- [🕒 How It Works](How-It-Works.md), for the rest of the page: the dispatches,
  the randomness, the authorship and the licensing.
- [`src/masthead.py`](src/masthead.py), the frames and the counting.
- [`src/cards.py`](src/cards.py), the renderer, the plate and the `<picture>`.
- [`tests/masthead.py`](tests/masthead.py), which walks every line the
  generator can write.
- [tannergolden/standards](https://github.com/tannergolden/standards), the
  documentation and commit conventions this file follows.

---

<div align="center">

**Twelve lines nobody wrote, from a thousand somebody did.**

[↑ Back to Top](#top)

</div>
