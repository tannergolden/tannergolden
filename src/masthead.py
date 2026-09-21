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

    def fill(self, pick) -> str:
        body = self.shape.format(*pick)
        return f"{self.emoji} {body}" if self.emoji else body

    def every(self):
        for pick in itertools.product(*self.slots):
            yield self.fill(pick)

    def draw(self) -> str:
        return self.fill([_RNG.choice(pool) for pool in self.slots])


FRAMES = (
    # --- what the work is --------------------------------------------------
    Frame("\U0001F512", "{} {} {}", (
        ("Hardening", "Gating", "Auditing"),
        ("every action", "every workflow", "every build"),
        ("by default", "before it merges"),
    )),
    Frame("\U0001F680", "{} {} {}", (
        ("Shipping", "Releasing", "Deploying"),
        ("a change", "a fix", "a version"),
        ("behind a gate", "with a rollback ready"),
    )),
    Frame("\U0001F552", "{} {} {}", (
        ("Reviewing", "Merging", "Shipping"),
        ("small changes", "one thing"),
        ("every day", "while it is fresh"),
    )),
    Frame("\U0001F510", "{} least {}, always", (
        ("Grant", "Request", "Assume", "Default to"),
        ("privilege", "access", "trust", "permission"),
    )),
    Frame("\u26D3\uFE0F", "{} that cannot {}", (
        ("A pipeline", "A gate", "A default", "A rule"),
        ("be skipped", "drift", "be argued away", "rot quietly"),
    )),
    # --- what it is for ----------------------------------------------------
    Frame("\u267B\uFE0F", "{} that {}", (
        ("Pipelines", "Standards", "Environments", "Guardrails"),
        ("outlive their author", "still run next year", "nobody has to remember",
         "explain themselves"),
    )),
    Frame("\U0001F4D6", "{} nobody {}", (
        ("Docs", "Standards", "Runbooks", "Guides"),
        ("has to read twice", "argues with", "can ignore", "has to guess at"),
    )),
    Frame("\U0001F9EA", "{} that {}", (
        ("Tests", "Gates", "Checks", "Linters"),
        ("catch it before I do", "fail for the right reason", "nobody can skip",
         "earn their runtime"),
    )),
    Frame("\U0001F4A4", "{} that {}", (
        ("Alerts", "Pipelines", "Builds", "Deploys"),
        ("nobody gets paged for", "wait until morning", "do not wake anyone",
         "run without me"),
    )),
    Frame("\U0001F9FE", "{} that says {}", (
        ("An error", "A log line", "A failure"),
        ("what to do", "what broke", "what comes next", "who to ask"),
    )),
    # --- preferences, stated as preferences --------------------------------
    Frame("\U0001F9ED", "{} over {}", (
        ("Boring tools", "One way", "Plain defaults", "Written rules"),
        ("configuration", "cleverness", "tribal knowledge", "heroics", "novelty"),
    )),
    Frame("\U0001F9F0", "{} I would {} again", (
        ("Tools", "Defaults", "Choices", "Conventions"),
        ("pick", "defend", "write", "make"),
    )),
    Frame("\U0001F3AF", "{} exactly {}", (
        ("Does", "Solves", "Covers"),
        ("one thing", "what it claims", "what is needed", "nothing more"),
    )),
    Frame("\U0001F3D7\uFE0F", "{} the {} way easy", (
        ("Make", "Keep", "Leave"),
        ("right", "safe", "boring"),
    )),
    Frame("\U0001F4CB", "{} once, {} everywhere", (
        ("Written", "Decided", "Fixed"),
        ("applied", "enforced", "used", "honoured"),
    )),
    # --- where the effort goes ---------------------------------------------
    Frame("\U0001F9F9", "{} {}", (
        ("Automating", "Documenting", "Simplifying", "Untangling"),
        ("the boring parts", "what people forget", "the thing nobody checks",
         "the step everyone skips"),
    )),
    Frame("\u2702\uFE0F", "{} more than I {}", (
        ("Deleting", "Removing", "Cutting", "Pruning"),
        ("add", "write", "ship", "merge"),
    )),
    Frame("\U0001F4E6", "{} {} once", (
        ("Defining", "Solving", "Writing", "Deciding"),
        ("the hard part", "the same problem", "the rule", "the answer"),
    )),
    Frame("\U0001F4C9", "One fewer {} to {}", (
        ("thing", "step", "decision", "moving part"),
        ("remember", "maintain", "explain", "get wrong"),
    )),
    Frame("\U0001F6AE", "{} removed, not {}", (
        ("Dead code", "Old flags", "Stale docs"),
        ("commented out", "left to rot", "quietly deprecated", "kept just in case"),
    )),
    # --- the supply chain --------------------------------------------------
    Frame("\U0001F4CC", "{}, not {}", (
        ("Pinned to a SHA", "Pinned to a digest", "Locked to a version",
         "Bound to a lockfile"),
        ("a tag", "latest", "a range", "a moving branch"),
    )),
    Frame("\U0001F517", "No {} without {}", (
        ("dependency", "action", "image", "package"),
        ("a pinned digest", "a known licence", "a review", "an SBOM"),
    )),
    Frame("\U0001F3F7\uFE0F", "Every {} carries {}", (
        ("release", "build", "commit", "image"),
        ("a version", "its provenance", "a changelog", "a signature"),
    )),
    Frame("\U0001F9CA", "{} frozen at {}", (
        ("The toolchain", "The base image", "The runtime", "The lockfile"),
        ("a digest", "a version", "a date", "a known good"),
    )),
    Frame("\U0001F5D3\uFE0F", "{} on a schedule, not {}", (
        ("Renewed", "Rotated", "Reviewed"),
        ("a whim", "a reminder", "a memory", "good intentions"),
    )),
    # --- reproducibility ---------------------------------------------------
    Frame("\u2699\uFE0F", "{} works on {}", (
        ("It", "The build", "The pipeline", "Every step"),
        ("my machine", "a fresh clone", "a cold runner", "a clean container"),
    )),
    Frame("\U0001F501", "{} twice and {}", (
        ("Run it", "Build it", "Deploy it", "Clone it"),
        ("get the same answer", "nothing differs", "the hash matches",
         "it still works"),
    )),
    Frame("\U0001F5FA\uFE0F", "{} with one {}", (
        ("Set up", "Reproduced", "Deployed", "Restored"),
        ("command", "clone", "file", "flag"),
    )),
    Frame("\U0001F9EC", "{} reproducible from {}", (
        ("A result", "A model", "A build", "A figure"),
        ("the commit alone", "a lockfile", "one command", "the manifest"),
    )),
    Frame("\U0001F52D", "{} another {} can {}", (
        ("Results", "Work", "Code"),
        ("team", "reviewer", "lab"),
        ("check", "rerun"),
    )),
    # --- operating it ------------------------------------------------------
    Frame("\U0001F9EF", "{} without {}", (
        ("Recovery", "A rollback", "A fix", "Failover"),
        ("a war room", "a pager", "a heroic night", "anyone noticing"),
    )),
    Frame("\U0001F514", "{} only when {}", (
        ("Notify", "Page", "Alert", "Interrupt"),
        ("it is real", "a human can help", "it cannot wait", "something broke"),
    )),
    Frame("\U0001F6DF", "{} when {}", (
        ("A way back", "A rollback", "An escape hatch", "A safe default"),
        ("it goes wrong", "nobody is watching", "the fix is slow", "it matters"),
    )),
    Frame("\U0001FA7A", "{} before {} does", (
        ("Catch it", "Find it", "Fix it", "Notice it"),
        ("a user", "the pager", "the customer", "anyone else"),
    )),
    Frame("\U0001FAAB", "{} that degrade {}", (
        ("Systems", "Services", "Builds"),
        ("gracefully", "loudly", "into a known state", "without losing data"),
    )),
    # --- what you can see --------------------------------------------------
    Frame("\U0001F50D", "{} you can actually {}", (
        ("Logs", "Traces", "Errors", "Metrics"),
        ("grep", "read", "act on", "trust"),
    )),
    Frame("\U0001FAB5", "{} in one {}", (
        ("The whole story", "Every request", "The failure", "The context"),
        ("line", "place", "query", "trace"),
    )),
    Frame("\U0001F9EE", "{} measured, not {}", (
        ("Latency", "Coverage", "Risk", "Cost"),
        ("guessed", "argued", "assumed", "felt"),
    )),
    Frame("\U0001F4A1", "{} obvious in {}", (
        ("The next step", "The failure", "The fix", "The intent"),
        ("the error", "the diff", "the name", "the log"),
    )),
    Frame("\U0001F4CA", "{} you can {} later", (
        ("Numbers", "Runs", "Results", "Experiments"),
        ("rerun", "compare", "defend", "reproduce"),
    )),
    # --- secrets -----------------------------------------------------------
    Frame("\U0001F5DD\uFE0F", "{} that never {}", (
        ("Secrets", "Tokens", "Keys", "Credentials"),
        ("reach a log", "leave the vault", "live in a repo", "get copied around"),
    )),
    Frame("\U0001F39A\uFE0F", "{} off by default, {} on", (
        ("Magic", "Guessing", "Retries", "Auto-merge"),
        ("checks", "gates", "logs", "limits"),
    )),
    # --- shape and review --------------------------------------------------
    Frame("\U0001FA9E", "{} before {}", (
        ("Review", "Test", "Lint", "Document"),
        ("a merge", "a release", "the pager rings", "anyone asks"),
    )),
    Frame("\U0001F4D0", "{} with {}", (
        ("One way in", "One shape", "A single entry point", "One source of truth"),
        ("no exceptions", "nothing hidden", "no side doors", "no surprises"),
    )),
    Frame("\U0001F4AC", "{} that reads as {}", (
        ("Code", "A commit", "A name", "An error"),
        ("prose", "a sentence", "its intent", "what it does"),
    )),
    Frame("\U0001F9E9", "{} that fit {}", (
        ("Pieces", "Repos", "Tools", "Standards"),
        ("together", "one job each", "without glue", "by contract"),
    )),
    Frame("\U0001F5C3\uFE0F", "{} where {} expects", (
        ("Files", "Configs", "Scripts", "Docs"),
        ("the next person", "everyone", "the tooling", "a newcomer"),
    )),
    # --- decay, and refusing it --------------------------------------------
    Frame("\U0001F331", "{} ages {}", (
        ("Nothing here", "No pipeline", "No config", "No default"),
        ("badly", "into a mystery", "without warning", "silently"),
    )),
    Frame("\U0001F6A7", "{} is {}", (
        ("Nothing here", "No workflow", "No step", "No secret"),
        ("half-migrated", "copied twice", "waiting on me", "a special case"),
    )),
    Frame("\u23F3", "{} that {} later", (
        ("Decisions", "Shortcuts", "Assumptions", "Cleverness"),
        ("cost nothing", "surface", "get paid for", "come back"),
    )),
    Frame("\U0001F50B", "{} that outlasts {}", (
        ("A convention", "A default", "A runbook", "A template"),
        ("the team", "the tool", "my memory", "the rewrite"),
    )),
    Frame("\U0001FA84", "No {} in {}", (
        ("magic", "surprises", "hidden state", "implicit steps"),
        ("the build", "the deploy", "the config", "the path"),
    )),
    # --- research that holds up --------------------------------------------
    Frame("\U0001F52C", "{} that survive {}", (
        ("Results", "Findings", "Benchmarks", "Claims"),
        ("a rerun", "review", "a new seed", "another machine"),
    )),
    Frame("\U0001F39B\uFE0F", "Never {} the same {} twice", (
        ("configure", "solve", "debug", "explain"),
        ("thing", "problem", "way", "step"),
    )),
    Frame("\U0001F6E0\uFE0F", "Fix the {}, not the {}", (
        ("class", "root", "cause", "pattern"),
        ("case", "symptom", "instance", "ticket"),
    )),
    # --- delivery ----------------------------------------------------------
    Frame("\U0001F4EE", "{} that arrives {}", (
        ("A change", "A release", "A fix", "A feature"),
        ("reviewed", "tested", "with a rollback", "or not at all"),
    )),
    Frame("\u23F1\uFE0F", "{} in under {}", (
        ("Builds", "Tests", "Feedback", "A review"),
        ("a minute", "five minutes", "ten minutes", "a coffee"),
    )),
    Frame("\U0001F6A6", "A red {} means {}", (
        ("build", "check", "gate", "test"),
        ("nobody merges", "it stops here", "work now", "the queue waits"),
    )),
    # --- the next person ---------------------------------------------------
    Frame("\U0001F393", "Only what the next {} {}", (
        ("person", "reader", "maintainer", "engineer"),
        ("needs", "will ask", "cannot guess", "would look for"),
    )),
    Frame("\U0001F4DD", "{} written down, not {}", (
        ("Decisions", "Conventions", "Trade-offs", "Reasons"),
        ("remembered", "argued", "re-derived", "guessed"),
    )),
    Frame("\U0001F310", "{} that works {}", (
        ("A default", "A setup", "An environment"),
        ("offline", "anywhere", "without me", "on any runner"),
    )),
    Frame("\U0001F9F1", "{} from parts that {}", (
        ("Built", "Assembled", "Composed", "Made"),
        ("are replaceable", "do one thing", "exist already", "nobody owns"),
    )),
    # --- the page talking about itself -------------------------------------
    Frame("\U0001F3B2", "{}, {}", (
        ("Drawn at random", "Generated nightly", "Written by a workflow",
         "Committed unattended"),
        ("just now", "nobody pressed anything", "nobody chose when",
         "while I was asleep", "and never twice"),
    )),
    Frame("\U0001F916", "{} {}", (
        ("Nobody typed", "No human wrote", "A workflow drew", "No hand touched"),
        ("this line", "what you are reading", "any of this", "a word of this"),
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
    # The elementary symmetric polynomial of the frame sizes, at degree
    # LINES_PER_MASTHEAD. Walking the subsets instead would be correct and
    # take C(38, 12) steps, which is 2.7 billion; this is 38 x 12.
    sizes = [frame.combinations() for frame in FRAMES]
    totals = [1] + [0] * LINES_PER_MASTHEAD
    for size in sizes:
        for k in range(LINES_PER_MASTHEAD, 0, -1):
            totals[k] += totals[k - 1] * size
    return totals[LINES_PER_MASTHEAD]


# --- the commit the schedule writes -------------------------------------------
#
# Held to the same standard as every other generated commit here, and drawn
# rather than written for the same reason the lines are: a log with the same
# paragraph in it twice a day is a log nobody reads twice. Every combination
# is a real why, because the standard asks for one and a body that restates
# its subject is the failure that section is written against.

COMMIT_SUBJECT = Frame("", "{} {}", (
    ("redraw", "retype", "recompose", "reprint", "redeal", "refresh"),
    ("the masthead", "the twelve lines", "what the terminal types", "the lines up top"),
))

COMMIT_WHY = (
    Frame("", "The loop inside the image is finite, so a reader who {} sees it "
              "{}. A later draw is the only thing that can hand them something "
              "they have not read.", (
        ("stays", "lingers", "leaves the tab open", "reads to the end"),
        ("come round", "repeat", "start again", "return to the top"),
    )),
    Frame("", "Nothing in the image changes while it is on screen, because "
              "GitHub serves a committed file and strips the script that might "
              "have {}. Variety has to arrive {}.", (
        ("redrawn it", "changed it", "helped"),
        ("between visits", "between draws", "on a schedule or not at all"),
    )),
    Frame("", "{{}} lines replace the {{}} before them, drawn from {{}}. A set "
              "that differs is the only thing a returning reader can be given, "
              "since {}.", (
        ("the animation cannot", "the file is static",
         "nothing in it moves on its own"),
    )),
)

COMMIT_HOW = (
    Frame("", "Twice a day, because {} should not {}.", (
        ("a reader who comes back tomorrow", "somebody returning next week",
         "a second visit"),
        ("be read the same thing", "find the same lines", "meet the same set"),
    )),
    Frame("", "On a twelve-hour clock: {}, {}.", (
        ("often enough that a return visit differs",
         "frequent enough that coming back is worth it"),
        ("rarely enough that the log stays about the dispatches",
         "seldom enough that it never crowds the feed"),
    )),
)


def commit_messages() -> int:
    """Distinct commit bodies the schedule can write, the emoji aside."""
    return (COMMIT_SUBJECT.combinations()
            * sum(f.combinations() for f in COMMIT_WHY)
            * sum(f.combinations() for f in COMMIT_HOW))


def commit_parts(drawn: int) -> tuple:
    """A subject, a why and a cadence, each drawn rather than written."""
    why = _RNG.choice(COMMIT_WHY).draw()
    if "{}" in why:  # the frame that wants the numbers
        why = why.format(drawn, drawn, TOTAL_LINES)
    return COMMIT_SUBJECT.draw(), why, _RNG.choice(COMMIT_HOW).draw()


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
