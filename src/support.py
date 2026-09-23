# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The support clock: what is current, and how long the current thing has left.

WHY THIS AND NOT A STATISTIC. The two cards this replaces reported five public
repositories and zero stars, every day, forever. A number that does not move
is a number nobody reads twice. Every figure here moves on its own: a release
lands and the version changes, a day passes and the countdown shortens, and
one of the rows turns red without anybody touching the repository.

It is also the rare thing on a profile that is USEFUL rather than merely true.
"Python 3.10 stopped getting security fixes four months ago" is a sentence
somebody can act on. "89.4% Python" is not.

WHAT IS ON IT IS NOT A LIST SOMEBODY TYPED. The languages are whatever this
account actually publishes, read from the GitHub API and mapped onto the
products that have a support lifecycle; a language nobody writes here drops
off by itself, and one picked up next year appears the same way. The three
operating systems are fixed, because "what am I running" is the same question
for every reader.

The data is endoflife.date, a public catalogue of release and support dates,
CC-BY-SA 4.0. Every row carries where it came from.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from dataclasses import dataclass
from datetime import date, datetime, timezone

import net
from text import clean

API = "https://endoflife.date/api/{product}.json"
HOME = "https://endoflife.date/{product}"
GITHUB = "https://api.github.com"

# --- what the account actually writes ----------------------------------------------

# Linguist's name for a language, then what the page calls the thing that
# actually has a lifecycle and the product endoflife.date tracks it under. A
# language whose name is not here is not asked about.
#
# THE ROW IS NAMED AFTER THE RUNTIME, NOT THE LANGUAGE, because the version
# and the date describe the runtime. A row reading "Shell 5.3" linking to
# Bash asks the reader to work out the mapping; a row reading "Bash 5.3" does
# not. Where the two names coincide, which is most of them, nothing changes.
#
# A WRONG GUESS COSTS NOTHING. An unknown product answers 404, `net` returns
# None, and the row is simply absent. That is why this leans generous: it is
# cheaper to list a mapping that turns out not to exist than to leave a
# language off the clock because nobody checked.
RUNTIMES = {
    "Python": ("Python", "python"),
    "JavaScript": ("Node.js", "nodejs"),
    "TypeScript": ("TypeScript", "typescript"),
    "Ruby": ("Ruby", "ruby"),
    "Go": ("Go", "go"),
    "Rust": ("Rust", "rust"),
    "PHP": ("PHP", "php"),
    "Java": ("Java", "java"),
    "Kotlin": ("Kotlin", "kotlin"),
    "Swift": ("Swift", "swift"),
    "C#": (".NET", "dotnet"),
    "F#": (".NET", "dotnet"),
    "Elixir": ("Elixir", "elixir"),
    "Erlang": ("Erlang", "erlang"),
    "Perl": ("Perl", "perl"),
    "R": ("R", "r"),
    "Dart": ("Dart", "dart"),
    "Scala": ("Scala", "scala"),
    "Clojure": ("Clojure", "clojure"),
    "Shell": ("Bash", "bash"),
    "Zig": ("Zig", "zig"),
}

# Languages with no support lifecycle to report. A Makefile does not go end of
# life, and listing one here says so deliberately rather than by omission.
NO_LIFECYCLE = frozenset({
    "Makefile", "Dockerfile", "HTML", "CSS", "SCSS", "Less", "Markdown",
    "JSON", "YAML", "TOML", "XML", "SQL", "TeX", "Roff", "Vim Script",
    "Jupyter Notebook", "Batchfile", "PowerShell", "Assembly", "C", "C++",
    "Objective-C", "Nix", "HCL", "Procfile", "Text", "Gherkin", "Just",
})

# The three questions every reader has about the machine in front of them.
# Linux is the kernel rather than a distribution, because "Linux" names the
# kernel and choosing somebody's distribution for them would be an opinion
# this page has no business having.
PLATFORMS = (
    ("macOS", "macos"),
    ("Windows", "windows"),
    ("Linux kernel", "linux"),
)

# Windows lists every release twice, once for Enterprise and Education and
# once for Home and Pro, as cycles ending "-e" and "-w". They carry the same
# version and different end dates, Enterprise's being the longer. Home and Pro
# is the machine more readers are on and the earlier date, so it is the one
# that warns rather than reassures.
PREFER = {"windows": "-w"}

# How many languages reach the page. Enough for any real account, few enough
# that the table stays a table.
MAX_LANGUAGES = 10

# Under this many bytes and a language is a config file somebody committed
# once, not something this account writes.
MIN_BYTES = 2_000


@dataclass(frozen=True)
class Release:
    """One product, and the supported line a reader should be on."""

    name: str  # what the page calls it
    product: str  # the endoflife.date slug
    cycle: str  # the supported line: "3.14", "26", "11 25H2"
    latest: str  # the newest release on it
    released: date | None  # when that release landed
    ends: date | None  # when the line stops getting security fixes
    forever: bool = False  # a line with no announced end

    @property
    def url(self) -> str:
        return HOME.format(product=self.product)

    def row(self) -> dict:
        """What is written to state, and all the page needs to draw a row.

        Dates go out as dates, never as the sentence they will become. The
        page recomputes "4 years left" on every write, so the countdown is
        right on a day nothing was fetched.
        """
        return {
            "name": self.name,
            "product": self.product,
            "url": self.url,
            "cycle": self.cycle,
            "latest": self.latest,
            "released": self.released.isoformat() if self.released else None,
            "ends": self.ends.isoformat() if self.ends else None,
            "forever": self.forever,
        }


def _day(value) -> date | None:
    """A calendar date, or None for anything that is not one.

    A release date is a date, not an instant: "2030-10-31" is that day
    wherever you read it. Parsing it as a datetime would invent a midnight
    and a zone the catalogue never claimed.
    """
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _supported(cycles: list, product: str = "") -> dict | None:
    """The newest cycle still receiving security fixes.

    endoflife.date returns newest first and spells "not end of life" three
    ways: `false`, a date in the future, or the field missing entirely. All
    three mean supported, and a cycle that says `true` or carries a date in
    the past does not.
    """
    today = datetime.now(timezone.utc).date()
    alive = []
    for cycle in cycles:
        if not isinstance(cycle, dict):
            continue
        eol = cycle.get("eol")
        if eol is True:
            continue
        when = _day(eol)
        if when is not None and when < today:
            continue
        alive.append(cycle)
    if not alive:
        return None
    suffix = PREFER.get(product)
    if suffix:
        wanted = [c for c in alive if str(c.get("cycle", "")).endswith(suffix)]
        if wanted:
            return wanted[0]
    return alive[0]


# A cycle is an identifier in the catalogue's URLs, so Windows spells one
# "11-26h1-w". On a page it should read the way the release is named.
_EDITION = re.compile(r"-(?:e|w)$")
_HALF = re.compile(r"^\d{2}h\d$", re.IGNORECASE)


def pretty_cycle(cycle: str) -> str:
    """The catalogue's cycle identifier, as a person would write the release."""
    trimmed = _EDITION.sub("", str(cycle))
    return " ".join(p.upper() if _HALF.match(p) else p for p in trimmed.split("-"))


def fetch(name: str, product: str) -> Release | None:
    """One product's supported line, or None if it cannot be read.

    None is an ordinary answer. A product slug that does not exist answers
    404, a catalogue that changed shape parses to nothing, and either way the
    row is absent rather than wrong.
    """
    cycles = net.get_json(API.format(product=urllib.parse.quote(product)))
    if not isinstance(cycles, list):
        return None
    current = _supported(cycles, product)
    if current is None:
        return None
    eol = current.get("eol")
    return Release(
        name=clean(name),
        product=clean(product),
        cycle=clean(pretty_cycle(current.get("cycle") or "")),
        latest=clean(str(current.get("latest") or current.get("cycle") or "")),
        released=_day(current.get("latestReleaseDate") or current.get("releaseDate")),
        ends=_day(eol),
        forever=eol is False or eol is None,
    )


# --- the languages this account publishes -------------------------------------------

def profile_languages(login: str, token: str | None) -> list:
    """Every language across the account's public repositories, by bytes.

    Forks and archives are excluded: a fork reports the language of somebody
    else's work, and an archive reports what this account used to write. What
    is left is what it publishes now, which is the only thing a support clock
    on this page could honestly be about.
    """
    headers = net.github_headers(token)
    totals: dict = {}
    page = 1
    while page <= 4:  # 400 repositories is more than this is ever asked for
        repos = net.get_json_with_headers(
            f"{GITHUB}/users/{urllib.parse.quote(login)}/repos",
            {"per_page": "100", "page": str(page), "type": "owner", "sort": "pushed"},
            headers,
        )
        if not isinstance(repos, list) or not repos:
            break
        for repo in repos:
            if not isinstance(repo, dict) or repo.get("fork") or repo.get("archived"):
                continue
            url = str(repo.get("languages_url") or "")
            if not url.startswith(f"{GITHUB}/"):
                continue
            sizes = net.get_json_with_headers(url, None, headers)
            if not isinstance(sizes, dict):
                continue
            for language, size in sizes.items():
                if isinstance(size, int):
                    totals[clean(str(language))] = totals.get(clean(str(language)), 0) + size
        if len(repos) < 100:
            break
        page += 1
    ordered = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    return [name for name, size in ordered if size >= MIN_BYTES]


def runtimes_for(languages: list) -> list:
    """The runtimes to ask about, in the order the account writes them.

    One runtime per language, and a runtime only once: an account writing
    both C# and F# asks about .NET once rather than twice.
    """
    out: list = []
    for language in languages:
        found = RUNTIMES.get(language)
        if not found or any(slug == found[1] for _, slug in out):
            continue
        out.append(found)
        if len(out) >= MAX_LANGUAGES:
            break
    return out


def collect(login: str, token: str | None) -> list:
    """Every row of the clock: the platforms, then whatever this account writes.

    The platforms come first because they are the same question for every
    reader; the languages follow in the order this account writes them, most
    bytes first, which is the order somebody scanning the page would want.

    An empty list means the catalogue could not be read at all. The caller
    keeps the last good reading rather than publishing an empty table, so a
    bad afternoon at endoflife.date costs the page a day of freshness and
    nothing else.
    """
    found = [fetch(name, product) for name, product in PLATFORMS]
    for name, product in runtimes_for(profile_languages(login, token)):
        found.append(fetch(name, product))
    return [release.row() for release in found if release is not None]


def account_login() -> str:
    """Whose repositories to read. The workflow already knows."""
    return os.environ.get("GITHUB_REPOSITORY_OWNER") or "tannergolden"


def every_product() -> list:
    """Every (name, slug) this repository could ever ask about, deduplicated.

    Not what the clock draws: what the mapping table CLAIMS exists. The probe
    walks this so one run answers which slugs the catalogue actually carries,
    rather than only the handful today's languages happen to reach.
    """
    out: list = []
    for name, slug in (*PLATFORMS, *RUNTIMES.values()):
        if not any(seen == slug for _, seen in out):
            out.append((name, slug))
    return out


def audit(login: str, token: str | None) -> tuple:
    """What the probe reports: the account's languages, and every slug tried.

    Deliberately wider than `collect`. `collect` asks only about the products
    today's languages reach, so a mapping that is wrong stays invisible until
    somebody writes that language. This asks about all of them, which is how
    a guess in the table gets checked before it is ever needed.
    """
    languages = profile_languages(login, token)
    asked = {slug for _, slug in runtimes_for(languages)}
    tried = [(name, slug, slug in asked, fetch(name, slug)) for name, slug in every_product()]
    return languages, tried


def refresh() -> list:
    """Every row of the clock, read fresh, for whoever this run belongs to.

    The token is the one the workflow already holds: anonymous calls to the
    GitHub API are rate limited per runner IP, which is shared, so a refresh
    without it works until the afternoon somebody else on the same address
    has used the hour up.
    """
    return collect(account_login(), os.environ.get("GITHUB_TOKEN"))
