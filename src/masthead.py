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
    # What the work is. The three pools are genuinely interchangeable, which
    # is why this frame carries most of the space on its own.
    Frame("\U0001F512", "{} {} {}", (
        ("Hardening", "Gating", "Pinning", "Auditing", "Reviewing"),
        ("every action", "every workflow", "every build", "every dependency", "every release"),
        ("by default", "before it merges", "on every push", "so nobody has to", "every single time"),
    )),
    # What it is for.
    Frame("\u267B\uFE0F", "{} that {}", (
        ("Pipelines", "Standards", "Environments", "Workflows", "Guardrails", "Runbooks"),
        ("outlive their author", "still run next year", "nobody has to remember",
         "a new machine cannot break", "explain themselves", "fail loudly"),
    )),
    # The supply-chain line the rest of the account actually enforces.
    Frame("\U0001F4CC", "{}, not {}", (
        ("Pinned to a commit SHA", "Pinned to a digest", "Locked to a version"),
        ("a tag", "latest", "a range", "a promise"),
    )),
    # Where the effort goes. Split from the one below, because deleting what
    # people forget and automating more than I add are both nonsense, and one
    # frame holding all four verbs produced exactly that.
    Frame("\U0001F9F9", "{} {}", (
        ("Automating", "Documenting"),
        ("the boring parts", "what people forget", "the thing nobody checks"),
    )),
    Frame("\u2702\uFE0F", "{} more than I {}", (
        ("Deleting", "Removing"),
        ("add", "write", "ship"),
    )),
    # The oldest joke in the trade, subverted: the whole point of the work
    # below is that it also works somewhere that is not my machine.
    Frame("\u2699\uFE0F", "{} works on {}", (
        ("It", "The build", "The pipeline"),
        ("my machine", "a fresh clone", "a cold runner", "somebody else's laptop"),
    )),
    Frame("\U0001F4D6", "{} nobody {}", (
        ("Docs", "Standards", "Runbooks"),
        ("has to read twice", "argues with", "can ignore"),
    )),
    Frame("\U0001F9EA", "{} that {}", (
        ("Tests", "Gates", "Checks"),
        ("catch it before I do", "fail for the right reason", "nobody can skip"),
    )),
    # The page talking about itself, which it has earned: it really is
    # generated, and this really was drawn rather than written.
    Frame("\U0001F3B2", "{}, {}", (
        ("Drawn at random", "Generated on a schedule", "Written by a workflow",
         "Committed unattended"),
        # "at a moment nobody chose" reads well and pushes the longest
        # combination in this frame to nine words, one over the ceiling.
        ("just now", "nobody pressed anything", "nobody chose when",
         "while I was asleep"),
    )),
    Frame("\U0001F916", "{} {}", (
        ("Nobody typed", "No human wrote", "A workflow drew", "Something generated"),
        ("this line", "what you are reading"),
    )),
)


# The greeting runs once and these loop, so this is the whole of what a
# reader who stays sees repeating. Five puts the loop at 23.5 seconds.
LINES_PER_MASTHEAD = 5


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
