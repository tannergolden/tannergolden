# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The lines the masthead types out, drawn fresh on every page refresh.

`Hello World!` is always first, and everything after it is assembled here
rather than written down. Not from a word salad: a slot filled at random from
a pool that fits every other slot in its frame produces grammar by accident
and nonsense by default, and a masthead reading "Deploying the quantum
wombat" would undo the rest of the page.

Each frame instead carries its own pools, small enough to have been read end
to end, and every combination a frame can produce is a sentence somebody
would say. The emoji belongs to the frame, because an emoji drawn
independently of the words lands on the wrong one about as often as the
right one.

The space is finite, and `combinations()` says how large. It is not
infinite; it is deeper than the number of refreshes this page will ever
have, which is the property actually being bought.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

# The plate is as wide as its longest line, so this is a layout constraint
# before it is an editorial one. At 52 cells and an 18px monospace the image
# comes to 594px, which sits inside GitHub's column on a desktop and scales
# down on a phone rather than overflowing.
MAX_CELLS = 52

GREETING = "\U0001F44B\U0001F3FB Hello World!"

# The greeting plus every line the frames can produce. A round number is a
# promise rather than an accident, so the pools are sized to land on it and
# a test fails the day one of them drifts.
TOTAL_LINES = 1000

_RNG = random.SystemRandom()


def cells(line: str) -> int:
    """How many terminal cells a line occupies.

    An emoji takes two, as it does in a terminal, and a variation selector
    takes none. Counting Python characters instead would under-measure every
    line that starts with an emoji, which is all of them.
    """
    total = 0
    for char in line:
        if char == "\ufe0f":
            continue
        total += 2 if ord(char) > 0x2100 else 1
    return total


@dataclass(frozen=True)
class Frame:
    """One sentence shape, and the pools that fill it.

    Every pool in a frame is interchangeable with every other, which is what
    makes the product of their lengths a count of sentences rather than a
    count of strings.
    """

    emoji: str
    shape: str
    slots: tuple  # one tuple of options per {} in the shape, in order

    def combinations(self) -> int:
        total = 1
        for pool in self.slots:
            total *= len(pool)
        return total

    def every(self):
        for pick in itertools.product(*self.slots):
            yield f"{self.emoji} {self.shape.format(*pick)}"

    def draw(self) -> str:
        return f"{self.emoji} {self.shape.format(*(_RNG.choice(p) for p in self.slots))}"


FRAMES = (
    # What the work is. Three interchangeable pools, so this frame carries
    # more of the space than any other on its own.
    Frame("\U0001F512", "{} {} {}", (
        ("Hardening", "Gating", "Auditing", "Reviewing", "Checking", "Guarding", "Signing"),
        ("every action", "every workflow", "every build", "every dependency",
         "every release", "every image", "every artefact"),
        ("by default", "before it merges", "on every push", "so nobody has to",
         "every single time", "without being asked"),
    )),
    # What it is for.
    Frame("\u267B\uFE0F", "{} that {}", (
        ("Pipelines", "Standards", "Environments", "Workflows", "Guardrails",
         "Runbooks", "Defaults", "Templates", "Conventions", "Gates"),
        ("outlive their author", "still run next year", "nobody has to remember",
         "a new machine cannot break", "explain themselves", "fail loudly",
         "need no maintenance", "survive a rewrite", "age well", "nobody fights"),
    )),
    # The supply-chain line the rest of the account actually enforces.
    Frame("\U0001F4CC", "{}, not {}", (
        ("Pinned to a SHA", "Pinned to a digest", "Locked to a version",
         "Fixed to a revision", "Bound to a lockfile"),
        ("a tag", "latest", "a range", "a promise", "a moving branch",
         "whatever resolves today", "a floating pointer"),
    )),
    # Where the effort goes.
    Frame("\U0001F9F9", "{} {}", (
        ("Automating", "Documenting", "Simplifying", "Untangling", "Flattening"),
        ("the boring parts", "what people forget", "the thing nobody checks",
         "the step everyone skips", "the part that breaks", "the bit that bites"),
    )),
    Frame("\u2702\uFE0F", "{} more than I {}", (
        ("Deleting", "Removing", "Cutting", "Pruning"),
        ("add", "write", "ship", "merge", "keep"),
    )),
    # The oldest joke in the trade, subverted: the whole point of the work
    # below is that it also works somewhere that is not my machine.
    Frame("\u2699\uFE0F", "{} works on {}", (
        ("It", "The build", "The pipeline", "The whole thing", "Every step"),
        ("my machine", "a fresh clone", "a cold runner", "somebody else's laptop",
         "a clean container", "the first try", "a borrowed machine"),
    )),
    Frame("\U0001F4D6", "{} nobody {}", (
        ("Docs", "Standards", "Runbooks", "Guides", "Comments", "Rules"),
        ("has to read twice", "argues with", "can ignore", "needs explained",
         "has to guess at", "quietly works around"),
    )),
    Frame("\U0001F9EA", "{} that {}", (
        ("Tests", "Gates", "Checks", "Linters", "Reviews", "Alarms"),
        ("catch it before I do", "fail for the right reason", "nobody can skip",
         "run on every change", "mean something", "earn their runtime"),
    )),
    # Shipping, which is the part the guardrails exist to make dull.
    Frame("\U0001F680", "{} {} {}", (
        ("Shipping", "Releasing", "Deploying", "Rolling out", "Cutting"),
        ("a change", "a release", "a fix", "a version", "a build"),
        ("behind a gate", "with a rollback ready", "on a green build",
         "when the checks pass", "without a pager"),
    )),
    # Small changes, often, while they are still understood.
    Frame("\U0001F552", "{} {} {}", (
        ("Reviewing", "Merging", "Shipping", "Reverting", "Testing"),
        ("small changes", "one thing", "a single commit", "what I understand",
         "the smallest diff"),
        ("every day", "before lunch", "the same week", "while it is fresh"),
    )),
    # The preferences, stated as preferences.
    Frame("\U0001F9ED", "{} over {}", (
        ("Boring tools", "One way", "Plain defaults", "Written rules",
         "Shared conventions", "Working automation", "Fewer choices", "Dull tooling"),
        ("configuration", "cleverness", "tribal knowledge", "heroics", "novelty",
         "three ways", "trust", "surprise"),
    )),
    Frame("\U0001F4E6", "{} {} once", (
        ("Defining", "Solving", "Writing", "Deciding"),
        ("the hard part", "the same problem", "the rule", "the answer", "the shape"),
    )),
    # Nobody should be woken up by this.
    Frame("\U0001F4A4", "{} that {}", (
        ("Alerts", "Pipelines", "Builds", "Deploys", "Rollbacks"),
        ("nobody gets paged for", "wait until morning", "do not wake anyone",
         "run without me", "need no babysitting"),
    )),
    # The page talking about itself, which it has earned: it really is
    # generated, and this really was drawn rather than written.
    Frame("\U0001F3B2", "{}, {}", (
        ("Drawn at random", "Generated nightly", "Written by a workflow",
         "Committed unattended", "Chosen by chance", "Assembled from parts",
         "Picked by a machine"),
        ("just now", "nobody pressed anything", "nobody chose when",
         "while I was asleep", "and never twice", "on no schedule",
         "without being asked"),
    )),
    Frame("\U0001F916", "{} {}", (
        ("Nobody typed", "No human wrote", "A workflow drew", "Something generated",
         "No hand touched", "A cron produced"),
        ("this line", "what you are reading", "any of this", "a word of this",
         "the line above"),
    )),
)


LINES_PER_MASTHEAD = 12


def mastheads() -> int:
    """Distinct mastheads, which is what a visitor actually sees.

    Not the number of lines: a reader takes in the whole set at once, and two
    sets differing in one line are two different mastheads. Frames are drawn
    without replacement, so this sums the product over every combination of
    frames that can appear together.
    """
    total = 0
    for chosen in itertools.combinations(FRAMES, LINES_PER_MASTHEAD):
        product = 1
        for frame in chosen:
            product *= frame.combinations()
        total += product
    return total


def combinations() -> int:
    """Every distinct line the frames can produce, the greeting aside."""
    return sum(frame.combinations() for frame in FRAMES)


def every_line():
    """All of them, for a test that asserts the whole space is shippable."""
    for frame in FRAMES:
        yield from frame.every()


def lines(count: int = LINES_PER_MASTHEAD) -> list:
    """The greeting, then `count` lines drawn from distinct frames.

    Distinct frames rather than distinct lines: two draws from one frame
    share a shape, and a masthead that says the same sentence twice with
    different nouns reads worse than one that changes the subject.
    """
    frames = _RNG.sample(FRAMES, k=min(count, len(FRAMES)))
    return [GREETING] + [frame.draw() for frame in frames]
