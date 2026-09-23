# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Everything that writes Markdown: the commit message, the archive, the page.

THE PAGE IS EDITED ONLY BETWEEN MARKERS. Five regions of README.md are bounded
by HTML comments of the form `<!-- NAME:BEGIN -->` and `<!-- NAME:END -->`,
the same shape as the AUTO-INDEX markers in tannergolden/standards. Text
inside them is machine-owned and rewritten whole; text outside them is never
read, let alone changed. A missing marker is an error, not an invitation to
guess where the region went.

The archive is append-only. One file per month, a dispatch added at the end,
and nothing above it ever rewritten. `state/recent.json` is a small rolling
index of the newest entries kept alongside so the page can be rendered
without parsing Markdown back into data.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import masthead
import phrasing
from config import (
    ASSETS_DIR,
    AUTHOR_EMAIL,
    AUTHOR_NAME,
    AVAILABILITY_FILE,
    DISPATCH_DIR,
    DISPLAY_TIMEZONE,
    ENTRIES_COLLAPSED,
    ENTRIES_VISIBLE,
    README,
    STATE_DIR,
)
from sources import Dispatch
from text import clean, fence_for, fit_subject, md_block, md_inline, safe_url, wrap_body

RECENT_FILE = f"{STATE_DIR}/recent.json"
MODULES_FILE = f"{STATE_DIR}/modules.json"
REPO_URL = "https://github.com/tannergolden/tannergolden"


def local(when: datetime) -> datetime:
    return when.astimezone(ZoneInfo(DISPLAY_TIMEZONE))


def zone_abbreviation(when: datetime) -> str:
    return local(when).strftime("%Z")


# --- regions -----------------------------------------------------------------

def _markers(name: str) -> tuple:
    return f"<!-- {name}:BEGIN -->", f"<!-- {name}:END -->"


def replace_region(document: str, name: str, content: str, *, document_name: str = README) -> str:
    begin, end = _markers(name)
    start = document.find(begin)
    stop = document.find(end)
    if start < 0 or stop < 0 or stop < start:
        raise ValueError(f"{document_name} has no intact {name} region; refusing to write")
    start += len(begin)
    return f"{document[:start]}\n{content.strip()}\n{document[stop:]}"


def read_region(document: str, name: str, *, document_name: str = README) -> str:
    begin, end = _markers(name)
    start = document.find(begin)
    stop = document.find(end)
    if start < 0 or stop < 0:
        raise ValueError(f"{document_name} has no intact {name} region")
    return document[start + len(begin) : stop].strip()


def update_readme(regions: dict) -> bool:
    """Rewrite the named regions; return whether the file changed."""
    original = Path(README).read_text(encoding="utf-8")
    updated = original
    for name, content in regions.items():
        updated = replace_region(updated, name, content)
    if updated != original:
        Path(README).write_text(updated, encoding="utf-8")
        return True
    return False


# --- the commit message --------------------------------------------------------

def commit_message(entry: Dispatch) -> str:
    """The full message: house-conformant header, prose body, provenance, sign-off.

    Built as a string and written to a file for `git commit -F`; it is never
    passed through a shell. The trailer block ends with the author's sign-off
    because the author is a person and this is their standing certification
    for a generator they wrote and scheduled.
    """
    header = fit_subject(entry.commit_type, entry.scope, entry.emoji, entry.subject)
    parts = [header, "", wrap_body(entry.body)]

    provenance = [f"Source: {entry.source_url}"]
    if entry.attribution:
        provenance.append(f"Attribution: {clean(entry.attribution)}")
    provenance.append(f"License: {clean(entry.license)}")
    # One block, no blank line before the sign-off: git parses only the last
    # paragraph as trailers, so provenance in a paragraph of its own would
    # not be read as trailers at all.
    parts += ["", *provenance, f"Signed-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>"]
    return "\n".join(parts) + "\n"


def failure_commit_message(reason: str, when: datetime) -> str:
    """The commit that turns the badge red. Its own message, so it can be tested."""
    body = wrap_body(
        f"The run that started at {local(when):%H:%M %Z on %A, %B %d} failed with "
        f"{clean(reason)[:240]}. The badge on the page says so until a run "
        f"succeeds; nothing fetched is in this commit."
    )
    return (
        f"ci(dispatches): \u2699\ufe0f mark the last run as failed\n\n{body}\n\n"
        f"Signed-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>\n"
    )


def recovery_commit_message() -> str:
    """The commit that turns the badge back, after an earlier run left it red."""
    body = wrap_body(
        "An earlier run failed and left the badge red. This run succeeded, so the "
        "badge says so again. Nothing fetched is in this commit."
    )
    return (
        f"ci(dispatches): \U0001F552 mark the run passing again\n\n{body}\n\n"
        f"Signed-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>\n"
    )


def readme_commit_message(when: datetime, changed: list) -> str:
    stamp = local(when).strftime("%A, %B %d, %Y at %H:%M %Z")
    what = ", ".join(changed) if changed else "the page"
    body = wrap_body(
        phrasing.one_of(
            f"Refreshed {what} on {stamp}.",
            f"{what[:1].upper()}{what[1:]}, as of {stamp}.",
            f"On {stamp}, this run refreshed {what}.",
        )
        + " The moment was drawn from the same exponential distribution as a "
        "dispatch, so this lands at an unremarkable hour rather than on a cron "
        "boundary. Nothing outside the marked regions was read or written."
    )
    return (
        f"chore(readme): {phrasing.emoji_for('chore')} {phrasing.verb_for('readme')} the page\n\n"
        f"{body}\n\nSigned-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>\n"
    )


# --- the archive ------------------------------------------------------------------

DISPATCH_FRONTMATTER = """<!--
title: '\U0001F4E1 DISPATCHES, {month_name} {year}'
description: 'Every dispatch the workflow sent in {month_name} {year}, in the order it sent them, each with its source and license.'
tags: [dispatches, generated, {year}, {month_slug}]
category: dispatches
-->

<!-- markdownlint-disable MD041 -->

<div align="center">

# \U0001F4E1 DISPATCHES, {month_name_upper} {year}

<a name="top"></a>

**One dispatch per commit, sent at a moment nobody scheduled.**

_Appended, never rewritten._

</div>

---

"""


def dispatch_path(when: datetime) -> str:
    """dispatches/2026/September.md, not dispatches/2026/09.md.

    A month has a name and a reader knows it on sight; a two digit number
    is a sort key wearing a filename. Chronological order is recovered
    from the name where it is actually needed, which is only the index
    below.
    """
    stamp = local(when)
    return f"{DISPATCH_DIR}/{stamp:%Y}/{stamp:%B}.md"


def dispatch_anchor(when: datetime) -> str:
    return f"dispatch-{local(when):%Y%m%d-%H%M%S}"


def day_heading(when: datetime) -> str:
    stamp = local(when)
    return f"## {stamp:%A, %B} {stamp.day}, {stamp:%Y}"


def render_dispatch(entry: Dispatch, when: datetime) -> str:
    """One entry: a heading that is the entry, then when and what, then why.

    The title is the heading rather than a bold line under one, so the
    archive has a table of contents and every dispatch has a link of its own.
    The day is carried by the heading above a run of dispatches, written
    once per day, because a month of them reading only "09:28" tells a
    reader nothing about which September the 9:28 belongs to.
    """
    stamp = local(when)
    lines = [
        f'<a name="{dispatch_anchor(when)}"></a>',
        "",
        f"### {entry.emoji} {md_inline(entry.title)}",
        "",
        f"`{entry.commit_type}({entry.scope})` · {stamp:%H:%M} {stamp:%Z}",
        "",
    ]
    lines.append(md_block(wrap_body(entry.body)))

    provenance = f"[{md_inline(entry.source_name)}]({safe_url(entry.source_url)})"
    if entry.attribution:
        provenance += f" · {md_inline(entry.attribution)}"
    provenance += f" · {md_inline(entry.license)}"
    for label, url in entry.extra_links:
        provenance += f" · [{md_inline(label)}]({safe_url(url)})"
    lines += ["", f"_{provenance}_", "", "---", ""]
    return "\n".join(lines)


MONTH_FILE = re.compile(r"^(\d{4})/([A-Z][a-z]+)\.md$")
MONTH_NUMBER = {datetime(2000, n, 1, tzinfo=timezone.utc).strftime("%B"): n for n in range(1, 13)}


def update_month_index() -> bool:
    """Regenerate the month table in dispatches/README.md from the files on disk.

    Machine-owned between MONTHS markers, like the page's regions: the
    prose around it is written by hand and never touched.
    """
    months = []
    for path in Path(DISPATCH_DIR).glob("*/*.md"):
        match = MONTH_FILE.match(path.relative_to(DISPATCH_DIR).as_posix())
        if not match or match.group(2) not in MONTH_NUMBER:
            continue
        months.append((int(match.group(1)), MONTH_NUMBER[match.group(2)], match.group(2), path))
    rows = []
    # Newest first, by the month a name means rather than by the name.
    for year, _, name, path in sorted(months, reverse=True):
        count = path.read_text(encoding="utf-8").count('<a name="dispatch-')
        rows.append(f"| [{name} {year}]({year}/{name}.md) | {count} |")
    table = "| Month | Dispatches |\n| :--- | ---: |\n" + "\n".join(rows) if rows else "_Nothing sent yet._"
    index = Path(DISPATCH_DIR) / "README.md"
    if not index.exists():
        return False
    original = index.read_text(encoding="utf-8")
    updated = replace_region(original, "MONTHS", table, document_name=str(index))
    if updated != original:
        index.write_text(updated, encoding="utf-8")
        return True
    return False


def append_dispatch(entry: Dispatch, when: datetime) -> str:
    path = Path(dispatch_path(when))
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        stamp = local(when)
        path.write_text(
            DISPATCH_FRONTMATTER.format(
                year=stamp.year,
                month_name=stamp.strftime("%B"),
                month_name_upper=stamp.strftime("%B").upper(),
                month_slug=stamp.strftime("%B").lower(),
            ),
            encoding="utf-8",
        )
    heading = day_heading(when)
    opened = heading in path.read_text(encoding="utf-8")
    with open(path, "a", encoding="utf-8") as handle:
        if not opened:
            handle.write(f"{heading}\n\n")
        handle.write(render_dispatch(entry, when))
    update_month_index()
    return str(path)


# --- the rolling index ----------------------------------------------------------------

def load_recent() -> list:
    try:
        with open(RECENT_FILE, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return []
    return loaded if isinstance(loaded, list) else []


def record_recent(entry: Dispatch, when: datetime, path: str) -> list:
    recent = load_recent()
    recent.insert(
        0,
        {
            "at": when.isoformat(),
            "type": entry.commit_type,
            "scope": entry.scope,
            "title": clean(entry.title),
            "path": path,
            "anchor": dispatch_anchor(when),
        },
    )
    recent = recent[: ENTRIES_VISIBLE + ENTRIES_COLLAPSED + 5]
    Path(RECENT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(RECENT_FILE, "w", encoding="utf-8") as handle:
        json.dump(recent, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return recent


def dispatches_this_month(when: datetime) -> int:
    month = local(when).strftime("%Y-%m")
    count = 0
    for item in load_recent():
        try:
            if local(datetime.fromisoformat(item["at"])).strftime("%Y-%m") == month:
                count += 1
        except (KeyError, ValueError):
            continue
    # The rolling index is capped, so a busy month is counted from the file.
    path = Path(dispatch_path(when))
    if path.exists():
        count = max(count, path.read_text(encoding="utf-8").count('<a name="dispatch-'))
    return count


# --- the page regions -------------------------------------------------------------------

def _row(item: dict, today: date | None = None) -> str:
    """A row in the page's table, dated only when the date is not the heading's.

    Dispatches go quiet for more than a day about six times a year, so the
    three shown are often not all from the day the heading names, and a
    bare "22:41" under today's date would be read as today.
    """
    when = local(datetime.fromisoformat(item["at"]))
    stamp = f"{when:%H:%M}" if today and when.date() == today else f"{when:%b} {when.day}, {when:%H:%M}"
    link = f"{item['path']}#{item['anchor']}"
    return f"| {stamp} | `{item['type']}({item['scope']})` | [{md_inline(item['title'])}]({link}) |"


def _tag(path: str) -> str:
    """Eight hex characters of a file's hash, so a rewritten image gets a new URL.

    GitHub's image proxy caches by URL. Without this a badge turned red by a
    failed run could keep showing green for hours.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]
    except OSError:
        return "0"


def render_dispatches_region(recent: list, when: datetime, month_count: int) -> str:
    stamp = local(when)
    heading = f"### {stamp:%A, %B} {stamp.day}, {stamp:%Y}"
    # The month file does not exist until the month's first entry, so the badge
    # points at the archive until then rather than at a page that is not there.
    month_target = dispatch_path(when) if month_count else f"{DISPATCH_DIR}/"
    status_badge, month_badge = "assets/badges/dynamic/dispatches.svg", "assets/badges/dynamic/month.svg"
    badges = (
        f"[![Dispatch workflow status]({status_badge}?v={_tag(status_badge)})]({REPO_URL}/actions/workflows/dispatches.yml) "
        f"[![Dispatches this month]({month_badge}?v={_tag(month_badge)})]({month_target})"
    )
    table_head = "| Time | Commit | Dispatch |\n| :--- | :--- | :--- |"

    visible = recent[:ENTRIES_VISIBLE]
    earlier = recent[ENTRIES_VISIBLE : ENTRIES_VISIBLE + ENTRIES_COLLAPSED]

    today = local(when).date()
    lines = [heading, "", badges, ""]
    if visible:
        lines += [table_head, *[_row(item, today) for item in visible]]
    else:
        lines += [
            "_No dispatches yet. The first lands at a random moment within the "
            "next twelve hours or so; nothing here is on a schedule._"
        ]
    if earlier:
        lines += [
            "",
            "<details>",
            "<summary>Earlier News</summary>",
            "",
            table_head,
            *[_row(item, today) for item in earlier],
            "",
            "</details>",
        ]
    lines += [
        "",
        f"[All dispatches]({DISPATCH_DIR}/) · [How it works](How-It-Works.md) · "
        f"{month_count} in {stamp:%B}",
    ]
    return "\n".join(lines)


def load_modules() -> dict:
    try:
        with open(MODULES_FILE, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def save_modules(modules: dict) -> None:
    Path(MODULES_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(MODULES_FILE, "w", encoding="utf-8") as handle:
        json.dump(modules, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def render_modules_region(modules: dict) -> str:
    """The terminal tip: what the tool is, what this invocation does, the line."""
    tip = modules.get("tip")
    if not tip:
        return "_The terminal tip fills in on the first refresh._"

    example = clean(tip["example"], command=True)
    fence = fence_for(example)
    header = f"> **{md_inline(tip['command'])}**"
    summary = tip.get("summary")
    if summary:
        header += f" · {md_inline(summary)}"
    header += f" · [tldr]({safe_url(tip['url'])})"
    return "\n".join(
        [
            "> [!TIP]",
            header,
            ">",
            f"> {md_inline(tip['description'])}:",
            ">",
            f"> {fence}bash",
            f"> {example}",
            f"> {fence}",
        ]
    )


# The three states, keyed by what the workflow's dropdown sends: the badge
# message, and the palette token that carries its meaning. One pick, and the
# badge says exactly that. The emoji the dropdown shows are the health colours
# these tokens already render, so the badge carries the same signal without
# spending a character on it.
AVAILABILITY = {
    "role": ("Open to role", "green"),
    "consult": ("Open to consult", "yellow"),
    "none": ("Not Available", "red"),
}

AVAILABILITY_BADGE = f"{ASSETS_DIR}/badges/dynamic/availability.svg"


def load_availability() -> str:
    """The committed state, or the empty string when it has never been set."""
    try:
        with open(AVAILABILITY_FILE, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, ValueError):
        return ""
    state = loaded.get("state") if isinstance(loaded, dict) else None
    return state if state in AVAILABILITY else ""


def availability_badge_set(state: str) -> str:
    """The `--set` argument the emblems kit takes for this badge."""
    message, colour = AVAILABILITY[state]
    return f"availability={message}:{colour}"


def save_availability(state: str) -> None:
    if state not in AVAILABILITY:
        raise ValueError(f"unknown availability state: {state!r}")
    Path(AVAILABILITY_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(AVAILABILITY_FILE, "w", encoding="utf-8") as handle:
        json.dump({"state": state}, handle, indent=2)
        handle.write("\n")


def render_availability_region(state: str) -> str:
    """The badge, or nothing at all.

    An unset status renders as empty rather than as a guess. A profile that
    silently claims to be looking for work, or not to be, is worse than one
    that says nothing, and this badge is only ever set by hand.
    """
    if state not in AVAILABILITY:
        return ""
    message = AVAILABILITY[state][0]
    return (
        f"[![Availability: {message}]"
        f"({AVAILABILITY_BADGE}?v={_tag(AVAILABILITY_BADGE)})](./)"
    )


def availability_commit_message(state: str) -> str:
    """A hand-triggered change to the page, so it reads like one.

    The body carries a why rather than a restatement, per The Body Is Not
    Optional in the commit standard. The what is already in the subject,
    and a body that repeats it is the failure that section is written
    against. Two whys are available to a generated commit here, and both
    are real: why the status is stated at all, and why a workflow writes
    it rather than a person editing the page.
    """
    label = AVAILABILITY[state][0].lower()
    header = fit_subject("docs", "availability", phrasing.emoji_for("docs"),
                         f"{phrasing.verb_for('availability')} {label}")
    why = phrasing.one_of(
        f"The badge now reads {label}. Nobody can infer that from the rest "
        "of this page: commit activity says nothing about whether its author "
        "is looking for work, and a reader guessing from it would be wrong "
        "in both directions.",
        f"{label.capitalize()}, from this commit. Everything else here "
        "reports what other people published; this line reports something "
        "only its author knows, which is why it is picked from a dropdown "
        "rather than derived from anything.",
        f"The availability badge now reads {label}. It is stated rather "
        "than left unsaid, because a profile silent on this invites the "
        "reader to guess, and a guess is wrong about as often as it is "
        "right.",
    )
    how = phrasing.one_of(
        "The workflow writes it rather than a person editing the page, "
        "because the availability region is machine owned and the next "
        "render would discard a hand edit.",
        "It goes through the workflow because a hand edit inside a "
        "machine-owned region survives exactly until the next render.",
        "A person picks the value and the workflow writes it, since "
        "anything typed into that region directly is overwritten the next "
        "time the page is rendered.",
    )
    return "\n".join([header, "", wrap_body(f"{why}\n\n{how}"), "",
                       f"Signed-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>"]) + "\n"


def masthead_commit_message(lines: list) -> str:
    """A scheduled redraw, assembled the same way the lines it commits are.

    Drawn rather than written, because a log carrying the same paragraph
    twice a day is a log nobody reads twice. The body still has to be a why
    and not a restatement, per The Body Is Not Optional, so every frame it
    can draw from states one: why a redraw exists at all, and why it is on a
    clock when nothing else here is.
    """
    subject, why, how = masthead.commit_parts(max(len(lines) - 1, 0))
    header = fit_subject("chore", "masthead", phrasing.emoji_for("chore"), subject)
    return "\n".join([header, "", wrap_body(f"{why}\n\n{how}"), "",
                       f"Signed-off-by: {AUTHOR_NAME} <{AUTHOR_EMAIL}>"]) + "\n"


def render_updated_line(when: datetime) -> str:
    stamp = local(when)
    return f"Last updated {stamp:%H:%M} {stamp:%Z} on {stamp:%A, %B} {stamp.day}, {stamp:%Y}."


def month_badge_message(count: int) -> str:
    """Just the number. The badge's own label says what it counts."""
    return str(count)


def git_env_for_commit() -> dict:
    """Author is the person, always. The committer is whatever performed the write.

    Under Actions that is the Actions identity, which the workflow sets and
    this falls back to. On a laptop it is left to git's own configuration,
    so a run a person made by hand is not recorded as made by a machine.
    """
    env = dict(os.environ)
    env["GIT_AUTHOR_NAME"] = AUTHOR_NAME
    env["GIT_AUTHOR_EMAIL"] = AUTHOR_EMAIL
    if os.environ.get("GITHUB_ACTIONS") == "true":
        env.setdefault("GIT_COMMITTER_NAME", "github-actions[bot]")
        env.setdefault("GIT_COMMITTER_EMAIL", "41898282+github-actions[bot]@users.noreply.github.com")
    return env


def month_label(when: datetime) -> str:
    return re.sub(r"\s+", " ", local(when).strftime("%B %Y"))
