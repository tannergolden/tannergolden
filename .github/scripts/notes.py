#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Draw the README's Field Notes: five GitHub alerts, redrawn every Monday.

  python3 .github/scripts/notes.py README.md [--library .github/notes] [--tldr PAGES] [--today YYYY-MM-DD]
  python3 .github/scripts/notes.py README.md --offline      curated notes only, no network

Each week gets one alert of each kind, in GitHub's order: Note, Tip,
Important, Warning, Caution. For every alert a coin, seeded by the week,
decides where it comes from: the curated library in .github/notes (1,000
notes per kind), or a public dataset that is always current:

  Note       GitHub's changelog                      github.blog/changelog
  Tip        a tldr-pages command example            CC BY 4.0
  Important  the next runtime or tool to lose support   endoflife.date
  Warning    a high-severity advisory this week      GitHub Advisory Database, CC BY 4.0
  Caution    a vulnerability being exploited now     CISA Known Exploited Vulnerabilities

A source that cannot be read, or has nothing recent, hands its alert back
to the library, so the block is always whole. Curated notes are handed out
across the four levels so a week of them runs from beginner to
professional, and each level's pool is walked in a shuffled order that
takes about nineteen years to come round. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import random
import re
import sys
import tomllib
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

KINDS = ("note", "tip", "important", "warning", "caution")  # GitHub's alert order
LEVELS = ("beginner", "intermediate", "advanced", "professional")
FIELDS = ("level", "topic", "text")
START, END = "<!-- notes:start -->", "<!-- notes:end -->"
BANNED = {"\u2013": "an en dash", "\u2014": "an em dash", "\u2015": "a horizontal bar"}
OPEN_SHARE = 0.5  # the chance an alert comes from open data rather than the library
UA = "tannergolden-profile-notes"
# The README tells time in EST: the week and every day an alert shows are counted in UTC-5.
EST = dt.timezone(dt.timedelta(hours=-5), "EST")

CHANGELOG = "https://github.blog/changelog/feed/"
EOL = "https://endoflife.date/api/{product}.json"
ADVISORIES = "https://api.github.com/advisories?type=reviewed&severity={severity}&per_page=100&sort=published&direction=desc"
KEV = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
TLDR_PAGE = "https://github.com/tldr-pages/tldr/blob/main/pages/common/{name}.md"

# The runtimes, databases and platforms a developer is most likely to run, by endoflife.date slug.
PRODUCTS = {
    "python": "Python", "nodejs": "Node.js", "go": "Go", "ruby": "Ruby", "php": "PHP", "dotnet": ".NET",
    "postgresql": "PostgreSQL", "mysql": "MySQL", "redis": "Redis", "kubernetes": "Kubernetes",
    "ubuntu": "Ubuntu", "debian": "Debian", "alpine": "Alpine Linux", "django": "Django", "rails": "Ruby on Rails",
    "angular": "Angular", "electron": "Electron", "nginx": "nginx",
}
ECOSYSTEMS = {"pip", "npm", "go", "maven", "rubygems", "rust", "nuget", "composer", "actions", "pub", "swift"}


@dataclass
class Alert:
    kind: str
    label: str    # "Beginner · Git" for the library, "tldr-pages · tar" for open data
    text: str     # Markdown, one line
    source: str   # "" for the library, else the attribution it needs


# -- the library ----------------------------------------------------------------------------


def load_library(folder: Path) -> dict[str, list[dict]]:
    """Every kind's notes, validated: a bad entry fails the run with its file, number and what is wrong."""
    library: dict[str, list[dict]] = {}
    for kind in KINDS:
        path = folder / f"{kind}.toml"
        notes = tomllib.loads(path.read_text(encoding="utf-8")).get("note", [])
        for i, n in enumerate(notes, 1):
            missing = [f for f in FIELDS if not str(n.get(f, "")).strip()]
            if missing:
                raise SystemExit(f"{path}: note {i} is missing {', '.join(missing)}")
            if n["level"] not in LEVELS:
                raise SystemExit(f"{path}: note {i} has level {n['level']!r}; use one of {', '.join(LEVELS)}")
            for ch, name in BANNED.items():
                if ch in n["text"] or ch in n["topic"]:
                    raise SystemExit(f"{path}: note {i} contains {name}, which the standards ban")
        gaps = [lv for lv in LEVELS if not any(n["level"] == lv for n in notes)]
        if gaps:
            raise SystemExit(f"{path}: every level needs notes; missing {', '.join(gaps)}")
        library[kind] = notes
    return library


def week_of(day: dt.date) -> int:
    """Weeks since 1 January of year 1, a Monday: one more every Monday."""
    return (day.toordinal() - 1) // 7


def coin(week: int, kind: str) -> random.Random:
    """The week's random choices for one alert: the same all week, different every week."""
    return random.Random(hashlib.sha256(f"field-notes:{week}:{kind}".encode()).digest())


def curated(library: dict[str, list[dict]], kind: str, week: int) -> Alert:
    """Kind k takes level (week + k) mod 4, and walks that level's pool in a fixed shuffled order."""
    k = KINDS.index(kind)
    level = LEVELS[(week + k) % len(LEVELS)]
    pool = [n for n in library[kind] if n["level"] == level]
    order = list(range(len(pool)))
    random.Random(f"field-notes-order:{kind}:{level}").shuffle(order)
    n = pool[order[(week // len(LEVELS)) % len(pool)]]
    return Alert(kind, f"{level.title()} · {n['topic'].strip()}", n["text"].strip(), "")


# -- open data --------------------------------------------------------------------------------

Fetch = Callable[[str, dict], bytes]


def fetch_url(url: str, headers: dict) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def plain(text: str, limit: int = 240) -> str:
    """Text from outside, made safe: no HTML, no banned dash, no Markdown syntax, one line, clipped at a word."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s*[\u2014\u2015]\s*", " - ", text).replace("\u2013", "-")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[:limit - 1].rsplit(" ", 1)[0].rstrip(" ,.;:-") + "…"
    return re.sub(r"([\\`*_{}\[\]<>#|~])", r"\\\1", text)


def keep_code(text: str, limit: int = 160) -> str:
    """Like plain(), but a `code span` in the source stays a code span."""
    parts = (text or "").split("`")
    if len(parts) % 2 == 0:  # unbalanced: treat it all as prose
        return plain(text, limit)
    out = "".join(plain(p, limit) if i % 2 == 0 else f"`{p}`" for i, p in enumerate(parts))
    return out if len(out) <= limit + 20 else plain(text.replace("`", ""), limit)


def sentence(text: str) -> str:
    return text if text.endswith((".", "…")) else text + "."


def day_label(day: dt.date) -> str:
    return f"{day.day} {day.strftime('%b')}"


def changelog(rng: random.Random, today: dt.date, fetch: Fetch, **_) -> Alert | None:
    """A change GitHub shipped in the last seven days."""
    root = ET.fromstring(fetch(CHANGELOG, {}))
    recent = []
    for item in root.iter("item"):
        title, link, when = item.findtext("title"), item.findtext("link"), item.findtext("pubDate")
        if not (title and link and when):
            continue
        try:
            day = email.utils.parsedate_to_datetime(when.strip()).astimezone(EST).date()
        except (TypeError, ValueError):
            day = dt.datetime.strptime(when.strip()[:16], "%a, %d %b %Y").date()
        if 0 <= (today - day).days <= 7:
            recent.append((day, plain(title, 200), link.strip()))
    if not recent:
        return None
    day, title, link = rng.choice(sorted(recent))
    return Alert("note", f"GitHub changelog · {day_label(day)}", f"[{title}]({link})", "GitHub changelog")


def tldr(rng: random.Random, today: dt.date, tldr_dir: Path | None = None, **_) -> Alert | None:
    """One example from one tldr-pages page, with its placeholders made readable."""
    if not tldr_dir or not tldr_dir.is_dir():
        return None
    pages = sorted(tldr_dir.glob("*.md"))
    if not pages:
        return None
    page = rng.choice(pages)
    lines = page.read_text(encoding="utf-8").splitlines()
    examples = [(lines[i][2:].strip(), lines[i + 2].strip()) for i in range(len(lines) - 2)
                if lines[i].startswith("- ") and lines[i + 2].startswith("`") and lines[i + 2].endswith("`")]
    if not examples:
        return None
    what, command = rng.choice(examples)
    what = re.sub(r"\[([^\]]*)\]", r"\1", what).rstrip(":").strip()               # [c]reate -> create
    command = re.sub(r"\{\{\[([^|\]]+)\|([^\]]+)\]\}\}", r"\2", command.strip("`"))  # {{[-C|--directory]}} -> --directory
    command = re.sub(r"\{\{(.*?)\}\}", r"<\1>", command)                              # {{path/to/file}} -> <path/to/file>
    if "`" in command or len(command) > 160:
        return None
    what = keep_code(what, 160)
    name = page.stem
    return Alert("tip", f"tldr-pages · [{name}]({TLDR_PAGE.format(name=name)})",
                 f"{what[0].upper() + what[1:]}: `{command}`", "tldr-pages (CC BY 4.0)")


def end_of_life(rng: random.Random, today: dt.date, fetch: Fetch, **_) -> Alert | None:
    """A release losing support in the next six months, or one that lost it in the last three."""
    soon, lately = [], []
    for slug in sorted(PRODUCTS):
        try:
            cycles = json.loads(fetch(EOL.format(product=slug), {}))
        except urllib.error.HTTPError:  # a product the site no longer lists; a network failure still raises
            continue
        if not isinstance(cycles, list) or not cycles:
            continue
        newest = str(cycles[0].get("cycle", ""))
        for c in cycles:
            eol = c.get("eol")
            if not isinstance(eol, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", eol):
                continue
            day = dt.date.fromisoformat(eol)
            entry = (day, slug, str(c.get("cycle", "")), newest)
            if 0 <= (day - today).days <= 183:
                soon.append(entry)
            elif 0 < (today - day).days <= 92:
                lately.append(entry)
    pick = rng.choice(sorted(soon)) if soon else (rng.choice(sorted(lately)) if lately else None)
    if not pick:
        return None
    day, slug, cycle, newest = pick
    name, when = PRODUCTS[slug], f"{day.day} {day.strftime('%B %Y')}"
    move = f" Move to {newest}, the newest release." if newest and newest != cycle else ""
    if day >= today:
        text = f"{name} {cycle} stops getting security fixes on {when}.{move}"
    else:
        text = f"{name} {cycle} stopped getting security fixes on {when}; anything still on it is exposed.{move}"
    return Alert("important", f"End of life · [{name} {cycle}](https://endoflife.date/{slug})", plain(text, 260), "endoflife.date")


def advisory(rng: random.Random, today: dt.date, fetch: Fetch, token: str = "", **_) -> Alert | None:
    """A reviewed critical or high advisory published in the last seven days, in a common ecosystem."""
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    recent = []
    for severity in ("critical", "high"):
        for a in json.loads(fetch(ADVISORIES.format(severity=severity), headers)):
            stamp = str(a.get("published_at") or "0001-01-01T00:00:00+00:00").replace("Z", "+00:00")
            published = dt.datetime.fromisoformat(stamp).astimezone(EST).date()
            if not 0 <= (today - published).days <= 7:
                continue
            for v in a.get("vulnerabilities") or []:
                pkg = (v.get("package") or {})
                if pkg.get("ecosystem") in ECOSYSTEMS and pkg.get("name"):
                    recent.append((a["ghsa_id"], a.get("summary", ""), a.get("html_url", ""), pkg["ecosystem"], pkg["name"],
                                   v.get("vulnerable_version_range") or "", v.get("first_patched_version") or ""))
                    break
    if not recent:
        return None
    ghsa, summary, url, ecosystem, name, affected, fixed = rng.choice(sorted(recent))
    fix = f" Update to `{plain(fixed, 40)}` or later." if fixed else " No fixed version yet: follow the advisory."
    where = f" ({plain(affected, 60)})" if affected else ""
    text = f"`{plain(name, 80)}`{where}: {sentence(plain(summary, 150))}{fix}"
    return Alert("warning", f"Advisory · [{ghsa}]({url}) · {ecosystem}", text, "GitHub Advisory Database (CC BY 4.0)")


def exploited(rng: random.Random, today: dt.date, fetch: Fetch, **_) -> Alert | None:
    """A vulnerability CISA added to its known-exploited catalog in the last fourteen days."""
    data = json.loads(fetch(KEV, {}))
    recent = [v for v in data.get("vulnerabilities", [])
              if 0 <= (today - dt.date.fromisoformat(v.get("dateAdded", "0001-01-01"))).days <= 14]
    if not recent:
        return None
    v = rng.choice(sorted(recent, key=lambda v: v["cveID"]))
    cve = v["cveID"]
    what = plain(f"{v.get('vendorProject', '')} {v.get('product', '')}: {v.get('vulnerabilityName', '')}", 140)
    action = plain(v.get("requiredAction", ""), 140)
    return Alert("caution", f"Actively exploited · [{cve}](https://nvd.nist.gov/vuln/detail/{cve})",
                 f"{sentence(what)} {sentence(action)}".strip(), "CISA KEV")


OPEN = {"note": changelog, "tip": tldr, "important": end_of_life, "warning": advisory, "caution": exploited}


# -- the block --------------------------------------------------------------------------------


def choose(library: dict, today: dt.date, fetch: Fetch | None, share: float = OPEN_SHARE, **ctx) -> list[Alert]:
    """One alert per kind: open data when the week's coin says so and the source answers, else the library."""
    week = week_of(today)
    alerts = []
    for kind in KINDS:
        rng = coin(week, kind)
        alert = None
        if fetch is not None and rng.random() < share:
            try:
                alert = OPEN[kind](rng, today, fetch=fetch, **ctx)
            except Exception as exc:  # a source that is down hands its alert back to the library
                print(f"::notice::{kind}: open data unavailable ({type(exc).__name__}: {exc}); a curated note stands in")
        alerts.append(alert or curated(library, kind, week))
    return alerts


def block(alerts: list[Alert], library: dict, today: dt.date) -> str:
    iso = today.isocalendar()
    body: list[str] = []
    for a in alerts:
        body += [f"> [!{a.kind.upper()}]", f"> **{a.label}.** {a.text}", ""]
    total = sum(len(v) for v in library.values())
    sources = [a.source for a in alerts if a.source]
    credit = f" Open data this week: {', '.join(sources)}." if sources else ""
    line = (f"<sub>Redrawn every Monday, at random, from {total:,} curated notes and five open data sources. "
            f"Week {iso.week} of {iso.year}.{credit}</sub>")
    out = "\n".join([START, "", *body, line, "", END])
    for ch, name in BANNED.items():
        if ch in out:
            raise SystemExit(f"the drawn block contains {name}")
    return out


def apply(readme: str, new_block: str) -> str:
    """The README with the block between the markers replaced. Nothing else moves."""
    if readme.count(START) != 1 or readme.count(END) != 1 or readme.index(START) > readme.index(END):
        raise SystemExit(f"the README needs exactly one {START} ... {END} pair")
    head, rest = readme.split(START, 1)
    _, tail = rest.split(END, 1)
    return head + new_block + tail


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("readme", type=Path)
    ap.add_argument("--library", type=Path, default=Path(".github/notes"))
    ap.add_argument("--tldr", type=Path, help="a checkout of tldr-pages' pages/common")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="the day to draw for, for reproducible output")
    ap.add_argument("--offline", action="store_true", help="curated notes only: read no open data")
    args = ap.parse_args(argv)
    today = args.today or dt.datetime.now(EST).date()
    library = load_library(args.library)
    alerts = choose(library, today, None if args.offline else fetch_url,
                    tldr_dir=args.tldr, token=os.environ.get("GH_TOKEN", ""))
    text = args.readme.read_text(encoding="utf-8")
    updated = apply(text, block(alerts, library, today))
    if updated != text:
        args.readme.write_text(updated, encoding="utf-8")
    iso = today.isocalendar()
    picked = ", ".join(f"{a.kind}: {a.source or 'library'}" for a in alerts)
    print(f"week {iso.week} of {iso.year} ({picked}): " + ("block redrawn" if updated != text else "nothing moved"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
