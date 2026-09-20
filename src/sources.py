# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The nine kinds of journal entry, and the picker that chooses between them.

Each fetcher returns one `Entry` the ledger has never seen, or None when its
source is down, empty for today, or exhausted. None is an ordinary answer: the
picker moves to the next kind, and a run in which every source fails writes
nothing and leaves the schedule untouched, so the next run tries again.

Nothing here is hand-written content. Every kind draws on a corpus that is
either enormous or still growing, which is what lets the ledger promise that
no item will ever appear twice: the promise costs nothing while the well is
deeper than the lifetime of the page.

Every string that leaves a fetcher has been through `text.clean()`.
"""

from __future__ import annotations

import hashlib
import random
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Callable

import net
from config import REPRODUCE_ROSETTA_CODE
from state import Ledger
from text import clamp_snippet, clean

_RNG = random.SystemRandom()


@dataclass
class Entry:
    """One journal entry, ready to be rendered into a commit and a page row."""

    kind: str  # the ledger key and the scope: unicode, rfc, xkcd, ...
    commit_type: str  # feat, fix, docs, refactor, test, chore
    emoji: str  # one emoji from the house mapping for that type
    subject: str  # lowercase imperative, without the type(scope) prefix
    title: str  # the short form shown in the page's journal row
    body: str  # prose for the commit body and the journal
    identifier: str  # what the ledger records; unique at the source
    source_name: str
    source_url: str
    license: str  # an SPDX identifier, or a short description when none fits
    attribution: str = ""  # authors or contributors, when the source names them
    code: str | None = None
    code_language: str | None = None
    code_trimmed: bool = False
    extra_links: list = field(default_factory=list)  # (label, url) pairs

    @property
    def scope(self) -> str:
        return self.kind


# --- helpers ----------------------------------------------------------------

def _shuffled(items: list) -> list:
    items = list(items)
    _RNG.shuffle(items)
    return items


def _first_unseen(ledger: Ledger, kind: str, candidates: list, key: Callable) -> object | None:
    for candidate in candidates:
        if not ledger.seen(kind, str(key(candidate))):
            return candidate
    return None


def _year_of(value: str) -> str:
    match = re.search(r"\b(\d{4})\b", value or "")
    return match.group(1) if match else ""


# --- feat(unicode) -----------------------------------------------------------

UCD = "https://www.unicode.org/Public/UCD/latest/ucd/UnicodeData.txt"
UCD_BLOCKS = "https://www.unicode.org/Public/UCD/latest/ucd/Blocks.txt"

# Blocks whose characters render in the fonts a browser ships with. Drawing
# from these four times in five keeps the glyph visible on the page; the fifth
# draw ranges over everything printable, so the long tail still appears.
PREFERRED_BLOCKS = {
    "Latin-1 Supplement", "Latin Extended-A", "Latin Extended-B", "IPA Extensions",
    "Greek and Coptic", "Cyrillic", "Armenian", "Hebrew", "Arabic", "Runic", "Ogham",
    "General Punctuation", "Currency Symbols", "Letterlike Symbols", "Number Forms",
    "Arrows", "Mathematical Operators", "Miscellaneous Technical", "Control Pictures",
    "Optical Character Recognition", "Enclosed Alphanumerics", "Box Drawing",
    "Block Elements", "Geometric Shapes", "Miscellaneous Symbols", "Dingbats",
    "Miscellaneous Mathematical Symbols-A", "Supplemental Arrows-A", "Braille Patterns",
    "Supplemental Arrows-B", "Miscellaneous Mathematical Symbols-B",
    "Supplemental Mathematical Operators", "Miscellaneous Symbols and Arrows",
    "Mahjong Tiles", "Domino Tiles", "Playing Cards", "Enclosed Alphanumeric Supplement",
    "Miscellaneous Symbols and Pictographs", "Emoticons", "Ornamental Dingbats",
    "Transport and Map Symbols", "Alchemical Symbols", "Geometric Shapes Extended",
    "Supplemental Arrows-C", "Supplemental Symbols and Pictographs", "Chess Symbols",
    "Symbols and Pictographs Extended-A", "Symbols for Legacy Computing",
}

# Names that are algorithmic rather than descriptive carry nothing to read.
UNINTERESTING_NAME = re.compile(
    r"^(<|CJK |TANGUT|NUSHU|KHITAN|HANGUL SYLLABLE|VARIATION SELECTOR|PRIVATE USE|SURROGATE|EGYPTIAN HIEROGLYPH-|CUNEIFORM (SIGN|NUMERIC)|LINEAR [AB] (SIGN|IDEOGRAM)|ANATOLIAN HIEROGLYPH)"
)
PRINTABLE_CATEGORIES = ("Lu", "Ll", "Lt", "Lo", "Nd", "Nl", "No", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So")


def _unicode_blocks() -> list:
    text = net.get_text(UCD_BLOCKS) or ""
    blocks = []
    for line in text.splitlines():
        match = re.match(r"^([0-9A-F]+)\.\.([0-9A-F]+); (.+)$", line)
        if match:
            blocks.append((int(match.group(1), 16), int(match.group(2), 16), match.group(3).strip()))
    return blocks


def _block_of(blocks: list, codepoint: int) -> str:
    for low, high, name in blocks:
        if low <= codepoint <= high:
            return name
    return "Unassigned"


def fetch_unicode(ledger: Ledger, today: date) -> Entry | None:
    text = net.get_text(UCD)
    if not text:
        return None
    blocks = _unicode_blocks()

    printable = []
    for line in text.splitlines():
        fields = line.split(";")
        if len(fields) < 3:
            continue
        name, category = fields[1], fields[2]
        if category not in PRINTABLE_CATEGORIES or UNINTERESTING_NAME.match(name):
            continue
        printable.append((int(fields[0], 16), name))
    if not printable:
        return None

    preferred = [item for item in printable if _block_of(blocks, item[0]) in PREFERRED_BLOCKS]
    pool = preferred if preferred and _RNG.random() < 0.8 else printable
    chosen = _first_unseen(ledger, "unicode", _shuffled(pool)[:400], key=lambda item: f"{item[0]:04X}")
    if chosen is None:
        return None

    codepoint, name = chosen
    glyph = chr(codepoint)
    block = _block_of(blocks, codepoint)
    hexname = f"U+{codepoint:04X}"
    name = clean(name)
    return Entry(
        kind="unicode",
        commit_type="feat",
        emoji="✨",
        subject=f"add {hexname} {glyph} {name}",
        title=f"{hexname} {glyph} {name}",
        body=(
            f"{hexname} is {name}, a character in the {block} block. "
            f"It renders as {glyph} and was chosen at random from every code point "
            f"with a descriptive name in the Unicode Character Database."
        ),
        identifier=f"{codepoint:04X}",
        source_name="Unicode Character Database",
        source_url=f"https://util.unicode.org/UnicodeJsps/character.jsp?a={codepoint:04X}",
        license="Unicode-3.0",
    )


# --- docs(rfc) ----------------------------------------------------------------

RFC_JSON = "https://www.rfc-editor.org/rfc/rfc{n}.json"
RFC_PAGE = "https://www.rfc-editor.org/rfc/rfc{n}"
RFC_CEILING = 9800

# A preference, not a list of content: half of all draws come from here while
# it lasts, because the point of an RFC entry is the one somebody has heard
# of. The other half ranges over the whole series, and once these are used
# up every draw does.
FAMOUS_RFCS = [
    1, 114, 675, 748, 791, 793, 821, 822, 959, 968, 1034, 1035, 1121, 1122, 1123,
    1149, 1180, 1216, 1217, 1321, 1437, 1438, 1855, 1918, 1925, 1945, 2026, 2045,
    2100, 2119, 2321, 2322, 2323, 2324, 2325, 2396, 2460, 2549, 2606, 2616, 2795,
    3091, 3092, 3093, 3164, 3251, 3252, 3339, 3514, 3986, 4041, 4042, 4122, 4180,
    4287, 4291, 4634, 4648, 5000, 5241, 5242, 5246, 5321, 5322, 5424, 5513, 5514,
    5841, 5984, 6214, 6217, 6238, 6265, 6455, 6585, 6592, 6749, 6797, 6902, 6919,
    6921, 7159, 7168, 7169, 7230, 7231, 7469, 7511, 7514, 7519, 7540, 7807, 8135,
    8136, 8140, 8174, 8200, 8259, 8367, 8446, 8565, 8771, 8774, 8962, 9000, 9110,
    9111, 9112, 9113, 9114, 9225, 9226, 9401, 9402, 9405, 9457, 9562,
]


def fetch_rfc(ledger: Ledger, today: date) -> Entry | None:
    famous = [n for n in FAMOUS_RFCS if not ledger.seen("rfc", str(n))]
    candidates: list = []
    if famous and _RNG.random() < 0.5:
        candidates = _shuffled(famous)[:6]
    while len(candidates) < 8:
        n = _RNG.randint(1, RFC_CEILING)
        if not ledger.seen("rfc", str(n)) and n not in candidates:
            candidates.append(n)

    for n in candidates:
        meta = net.get_json(RFC_JSON.format(n=n))
        if not isinstance(meta, dict) or not meta.get("title"):
            continue
        title = clean(str(meta.get("title", "")))
        if title.lower() in ("not issued", ""):
            continue
        year = _year_of(str(meta.get("pub_date", "")))
        abstract = clean(str(meta.get("abstract", "") or ""), allow_newlines=True)
        authors = ", ".join(clean(str(a)) for a in (meta.get("authors") or []) if a)
        status = clean(str(meta.get("status", "") or "")).lower()
        published = clean(str(meta.get("pub_date", "") or "")) or year

        opener = f"RFC {n}, {title!s}"
        if published:
            opener += f", was published in {published}"
        if status:
            opener += f", with the status {status}"
        opener += "."
        body = opener + ("\n\n" + abstract if abstract else "")

        return Entry(
            kind="rfc",
            commit_type="docs",
            emoji="\U0001F4DD",
            subject=f"record RFC {n}, {title}",
            title=f"RFC {n}: {title}",
            body=body,
            identifier=str(n),
            source_name="RFC Editor",
            source_url=RFC_PAGE.format(n=n),
            license="IETF Trust Legal Provisions; RFCs may be freely reproduced",
            attribution=authors,
        )
    return None


# --- docs(xkcd) ---------------------------------------------------------------

XKCD_LATEST = "https://xkcd.com/info.0.json"
XKCD_ITEM = "https://xkcd.com/{n}/info.0.json"


def fetch_xkcd(ledger: Ledger, today: date) -> Entry | None:
    latest = net.get_json(XKCD_LATEST)
    if not isinstance(latest, dict) or not isinstance(latest.get("num"), int):
        return None
    ceiling = latest["num"]

    tried = 0
    for _ in range(60):
        if tried >= 10:
            break
        n = _RNG.randint(1, ceiling)
        if n == 404 or ledger.seen("xkcd", str(n)):  # 404 famously does not exist
            continue
        tried += 1
        comic = net.get_json(XKCD_ITEM.format(n=n))
        if not isinstance(comic, dict) or not comic.get("title"):
            continue
        title = clean(str(comic.get("safe_title") or comic.get("title")))
        alt = clean(str(comic.get("alt", "")))
        if len(alt) > 320:
            alt = alt[:319].rsplit(" ", 1)[0] + "…"
        year = clean(str(comic.get("year", "")))
        body = f"xkcd {n}, {title!s}" + (f", from {year}." if year else ".")
        if alt:
            body += f'\n\nThe hover text reads: "{alt}"'
        return Entry(
            kind="xkcd",
            commit_type="docs",
            emoji="\U0001F4DD",
            subject=f"record xkcd {n}, {title}",
            title=f"xkcd {n}: {title}",
            body=body,
            identifier=str(n),
            source_name="xkcd",
            source_url=f"https://xkcd.com/{n}/",
            license="CC-BY-NC-2.5",
            attribution="Randall Munroe",
        )
    return None


# --- test(sequence) -----------------------------------------------------------

OEIS_SEARCH = "https://oeis.org/search"


def fetch_sequence(ledger: Ledger, today: date) -> Entry | None:
    keyword = "core" if _RNG.random() < 0.25 else "nice"
    first = net.get_json(OEIS_SEARCH, {"q": f"keyword:{keyword}", "fmt": "json", "start": 0})
    if not isinstance(first, dict):
        return None
    results = first.get("results") or []
    count = int(first.get("count") or len(results) or 0)
    if count <= 0:
        return None

    for _ in range(4):
        offset = _RNG.randrange(0, count)
        page = net.get_json(OEIS_SEARCH, {"q": f"keyword:{keyword}", "fmt": "json", "start": offset})
        if not isinstance(page, dict):
            continue
        candidates = [r for r in (page.get("results") or []) if isinstance(r, dict)]
        chosen = _first_unseen(ledger, "sequence", _shuffled(candidates), key=lambda r: r.get("number"))
        if chosen is None:
            continue
        number = int(chosen["number"])
        terms = [t for t in str(chosen.get("data", "")).split(",") if t.strip()]
        if len(terms) < 9:
            continue
        shown = terms[:8]
        answer = terms[8]
        name = clean(str(chosen.get("name", "")))
        a_number = f"A{number:06d}"
        puzzle = ", ".join(shown)
        return Entry(
            kind="sequence",
            commit_type="test",
            emoji="\U0001F9EA",
            subject=f"continue {puzzle}",
            title=f"{puzzle}, what comes next?",
            body=(
                f"The sequence begins {puzzle}. What comes next?\n\n"
                f"The next term is {answer}. This is {a_number}, {name}"
                + ("" if name.endswith(".") else ".")
            ),
            identifier=str(number),
            source_name="OEIS",
            source_url=f"https://oeis.org/{a_number}",
            license="CC-BY-SA-4.0",
        )
    return None


# --- refactor(rosetta) ----------------------------------------------------------

ROSETTA_API = "https://rosettacode.org/w/api.php"
ROSETTA_PAGE = "https://rosettacode.org/w/index.php"
HEADER = re.compile(r"^==\s*\{\{header\|([^}|]+)(?:\|[^}]*)?\}\}\s*==\s*$", re.MULTILINE)
CODE_BLOCK = re.compile(
    r"<(?:syntaxhighlight|lang)(?:\s+lang=\"?([^\">\s]+)\"?|\s+([^>\s]+))?[^>]*>(.*?)</(?:syntaxhighlight|lang)>",
    re.DOTALL | re.IGNORECASE,
)


def _rosetta_tasks() -> list:
    tasks: list = []
    params = {
        "action": "query", "list": "categorymembers", "cmtitle": "Category:Programming_Tasks",
        "cmlimit": "500", "cmnamespace": "0", "format": "json",
    }
    for _ in range(6):
        page = net.get_json(ROSETTA_API, params)
        if not isinstance(page, dict):
            break
        tasks.extend(m.get("title") for m in page.get("query", {}).get("categorymembers", []) if m.get("title"))
        cont = page.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params = dict(params, cmcontinue=cont)
    return tasks


def _rosetta_solutions(task: str) -> tuple:
    page = net.get_json(ROSETTA_API, {"action": "parse", "page": task, "prop": "wikitext|revid", "format": "json"})
    if not isinstance(page, dict) or "parse" not in page:
        return {}, 0
    wikitext = page["parse"].get("wikitext", {}).get("*", "")
    revid = int(page["parse"].get("revid") or 0)

    solutions = {}
    headers = list(HEADER.finditer(wikitext))
    for index, match in enumerate(headers):
        language = match.group(1).strip()
        end = headers[index + 1].start() if index + 1 < len(headers) else len(wikitext)
        block = CODE_BLOCK.search(wikitext[match.end():end])
        if not block or "/" in language:
            continue
        code = block.group(3).strip("\n")
        if code.strip():
            solutions[language] = (block.group(1) or block.group(2) or language.lower(), code)
    return solutions, revid


def fetch_rosetta(ledger: Ledger, today: date) -> Entry | None:
    tasks = _rosetta_tasks()
    if not tasks:
        return None

    # Two entries in five revisit a task already on the page in a language it
    # has not been shown in, which is what makes the type honest: a refactor
    # is the same thing done another way, and a running thread reads better
    # than a scatter of unrelated programs.
    used_tasks = sorted({pair.rsplit("|", 1)[0] for pair in ledger.used("rosetta")})
    order = _shuffled(tasks)
    if used_tasks and _RNG.random() < 0.4:
        order = _shuffled(used_tasks) + order

    for task in order[:5]:
        solutions, revid = _rosetta_solutions(task)
        languages = [lang for lang in solutions if not ledger.seen("rosetta", f"{task}|{lang}")]
        if not languages:
            continue
        language = _RNG.choice(languages)
        highlight, code = solutions[language]
        snippet, trimmed = clamp_snippet(code)
        again = task in used_tasks
        verb = "rewrite" if again else "solve"
        title = clean(task)
        permalink = f"{ROSETTA_PAGE}?title={task.replace(' ', '_')}&oldid={revid}" if revid else f"https://rosettacode.org/wiki/{task.replace(' ', '_')}"
        body = (
            f"The Rosetta Code task {title!s}, {'again, this time' if again else 'solved'} in {clean(language)}."
            + ("" if REPRODUCE_ROSETTA_CODE else " The code is at the link; this entry cites rather than reproduces it.")
        )
        return Entry(
            kind="rosetta",
            commit_type="refactor",
            emoji="♻️",
            subject=f"{verb} {title} in {clean(language)}",
            title=f"{title}, {'now' if again else 'solved'} in {clean(language)}",
            body=body,
            identifier=f"{task}|{language}",
            source_name="Rosetta Code",
            source_url=permalink,
            license="GFDL-1.2-only",
            attribution="Rosetta Code contributors",
            code=snippet if REPRODUCE_ROSETTA_CODE else None,
            code_language=clean(highlight).lower() if REPRODUCE_ROSETTA_CODE else None,
            code_trimmed=trimmed,
        )
    return None



# --- chore(release) and docs(born): Wikidata -------------------------------------

WDQS = "https://query.wikidata.org/sparql"

RELEASE_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?date ?links WHERE {{
  VALUES ?class {{ wd:Q7889 wd:Q7397 wd:Q9135 wd:Q9143 wd:Q166142 }}
  ?item wdt:P31 ?class ; wdt:P577 ?date ; wikibase:sitelinks ?links .
  FILTER(MONTH(?date) = {month} && DAY(?date) = {day} && ?links >= 5)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY DESC(?links) LIMIT 80
"""

BORN_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?itemDescription ?dob ?links WHERE {{
  VALUES ?occupation {{ wd:Q82594 wd:Q5482740 wd:Q183888 wd:Q210167 }}
  ?item wdt:P31 wd:Q5 ; wdt:P106 ?occupation ; wdt:P569 ?dob ; wikibase:sitelinks ?links .
  FILTER(MONTH(?dob) = {month} && DAY(?dob) = {day} && ?links >= 3)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} ORDER BY DESC(?links) LIMIT 80
"""


def _sparql(query: str) -> list:
    payload = net.get_json(WDQS, {"query": query, "format": "json"})
    if not isinstance(payload, dict):
        return []
    rows = []
    for binding in payload.get("results", {}).get("bindings", []):
        rows.append({key: value.get("value", "") for key, value in binding.items()})
    return rows


def _qid(uri: str) -> str:
    return uri.rsplit("/", 1)[-1]


def _weighted_by_links(rows: list) -> list:
    """Order rows by a weighted shuffle, so the famous lead without the obscure never appearing."""
    keyed = []
    for row in rows:
        links = max(int(float(row.get("links", "1") or 1)), 1)
        keyed.append((_RNG.random() ** (1.0 / links), row))
    keyed.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in keyed]


def fetch_release(ledger: Ledger, today: date) -> Entry | None:
    rows = _sparql(RELEASE_QUERY.format(month=today.month, day=today.day))
    rows = [r for r in rows if r.get("itemLabel") and not r["itemLabel"].startswith("Q")]
    chosen = _first_unseen(ledger, "release", _weighted_by_links(rows), key=lambda r: _qid(r["item"]))
    if chosen is None:
        return None

    label = clean(chosen["itemLabel"])
    description = clean(chosen.get("itemDescription", ""))
    year = int(_year_of(chosen.get("date", "")) or today.year)
    age = today.year - year
    qid = _qid(chosen["item"])
    version = f"v{age}.0.0"
    turns = f"{label} turns {age}" if age > 0 else f"{label} is released"
    body = f"{label}{', ' + description if description else ''}, was released on this date in {year}."
    if age > 0:
        body += f" That makes it {age} today, which is the major version number above: age is the only semver these anniversaries get."
    return Entry(
        kind="release",
        commit_type="chore",
        emoji="\U0001F9F9",
        subject=f"{version}, {turns}",
        title=turns,
        body=body,
        identifier=qid,
        source_name="Wikidata",
        source_url=f"https://www.wikidata.org/wiki/{qid}",
        license="CC0-1.0",
    )


def fetch_born(ledger: Ledger, today: date) -> Entry | None:
    rows = _sparql(BORN_QUERY.format(month=today.month, day=today.day))
    rows = [r for r in rows if r.get("itemLabel") and not r["itemLabel"].startswith("Q")]
    chosen = _first_unseen(ledger, "born", _weighted_by_links(rows), key=lambda r: _qid(r["item"]))
    if chosen is None:
        return None

    name = clean(chosen["itemLabel"])
    description = clean(chosen.get("itemDescription", ""))
    year = _year_of(chosen.get("dob", ""))
    qid = _qid(chosen["item"])
    body = f"{name}{', ' + description if description else ''}, was born on this date" + (f" in {year}." if year else ".")
    return Entry(
        kind="born",
        commit_type="docs",
        emoji="\U0001F4DD",
        subject=f"mark the birthday of {name}" + (f", {year}" if year else ""),
        title=f"{name}, born {year}" if year else name,
        body=body,
        identifier=qid,
        source_name="Wikidata",
        source_url=f"https://www.wikidata.org/wiki/{qid}",
        license="CC0-1.0",
    )


# --- fix(bug): Wikipedia -----------------------------------------------------------

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
BUG_PAGE = "List of software bugs"
WIKI_LINK = re.compile(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]")
WIKI_MARKUP = re.compile(r"'{2,}|<[^>]+>|\{\{[^}]*\}\}|<ref[^/]*/>|<ref.*?</ref>", re.DOTALL)


def _strip_wikitext(text: str) -> str:
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = WIKI_MARKUP.sub("", text)
    text = WIKI_LINK.sub(lambda m: m.group(2) or m.group(1), text)
    return clean(text)


def fetch_bug(ledger: Ledger, today: date) -> Entry | None:
    page = net.get_json(WIKIPEDIA_API, {"action": "parse", "page": BUG_PAGE, "prop": "wikitext|revid", "format": "json"})
    if not isinstance(page, dict) or "parse" not in page:
        return None
    wikitext = page["parse"].get("wikitext", {}).get("*", "")
    revid = page["parse"].get("revid", 0)

    items = []
    for line in wikitext.splitlines():
        if not line.startswith("*") or line.startswith("**"):
            continue
        raw = line.lstrip("* ").strip()
        first_link = WIKI_LINK.search(raw)
        prose = _strip_wikitext(raw)
        if len(prose) < 40:
            continue
        anchor = first_link.group(1) if first_link else prose[:60]
        items.append((hashlib.sha1(anchor.encode("utf-8")).hexdigest()[:12], anchor, prose))  # noqa: S324 - an identifier, not a credential

    chosen = _first_unseen(ledger, "bug", _shuffled(items), key=lambda item: item[0])
    if chosen is None:
        if items:
            ledger.retire("bug")
        return None

    identifier, anchor, prose = chosen
    excerpt = prose if len(prose) <= 400 else prose[:399].rsplit(". ", 1)[0] + "."
    name = clean(anchor.split("(")[0])
    return Entry(
        kind="bug",
        commit_type="fix",
        emoji="\U0001F41B",
        subject=f"revisit {name}",
        title=name,
        body=excerpt,
        identifier=identifier,
        source_name="Wikipedia, List of software bugs",
        source_url=f"https://en.wikipedia.org/w/index.php?title=List_of_software_bugs&oldid={revid}",
        license="CC-BY-SA-4.0",
        attribution="Wikipedia contributors",
    )


# --- fix(falsehood): awesome-falsehood ----------------------------------------------

FALSEHOOD_LIST = "https://raw.githubusercontent.com/kdeldycke/awesome-falsehood/main/readme.md"
LIST_ITEM = re.compile(r"^\s*[-*]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-:\u2013\u2014]?\s*(.*)$")


def fetch_falsehood(ledger: Ledger, today: date) -> Entry | None:
    text = net.get_text(FALSEHOOD_LIST)
    if not text:
        return None

    items = []
    for line in text.splitlines():
        match = LIST_ITEM.match(line)
        if not match:
            continue
        title, url, blurb = match.group(1), match.group(2), match.group(3)
        if "falsehood" not in title.lower() or not url.startswith("https://"):
            continue
        items.append((url, clean(title), clean(blurb)))

    chosen = _first_unseen(ledger, "falsehood", _shuffled(items), key=lambda item: item[0])
    if chosen is None:
        if items:
            ledger.retire("falsehood")
        return None

    url, title, blurb = chosen
    topic = re.sub(r"^falsehoods?\s+(programmers|developers|people)?\s*(believe|think)?\s*(about)?\s*", "", title, flags=re.IGNORECASE).strip(" .")
    return Entry(
        kind="falsehood",
        commit_type="fix",
        emoji="\U0001F41B",
        subject=f"correct what programmers believe about {topic or title}",
        title=title,
        body=(blurb or f"A catalogue of things programmers believe about {topic or 'the world'} that are not so.")
        + " Each one is an assumption that held on the machine it was written on and failed on the next.",
        identifier=url,
        source_name="awesome-falsehood",
        source_url=url,
        license="CC0-1.0 (the list); the article itself is not reproduced",
        extra_links=[("the list", "https://github.com/kdeldycke/awesome-falsehood")],
    )


# --- the picker -------------------------------------------------------------------

FETCHERS: dict = {
    "release": fetch_release,
    "born": fetch_born,
    "rosetta": fetch_rosetta,
    "unicode": fetch_unicode,
    "rfc": fetch_rfc,
    "xkcd": fetch_xkcd,
    "sequence": fetch_sequence,
    "bug": fetch_bug,
    "falsehood": fetch_falsehood,
}

COMMON = ("release", "born", "rosetta", "unicode", "rfc", "xkcd", "sequence")
RARE = ("bug", "falsehood")
RARE_SHARE = 0.05  # the two rare kinds together, while their lists last


def weights(retired: set) -> dict:
    """The draw weights: seven common kinds share what the rare pair does not take."""
    rare = [k for k in RARE if k not in retired]
    common = [k for k in COMMON if k not in retired]
    result = {}
    rare_total = RARE_SHARE if rare else 0.0
    for kind in rare:
        result[kind] = rare_total / len(rare)
    for kind in common:
        result[kind] = (1.0 - rare_total) / len(common)
    return result


def draw_order(retired: set) -> list:
    """Kinds in the order they will be tried: a weighted draw without replacement."""
    remaining = weights(retired)
    order = []
    while remaining:
        total = sum(remaining.values())
        point = _RNG.random() * total
        chosen = next(iter(remaining))
        for kind, weight in remaining.items():
            point -= weight
            chosen = kind
            if point <= 0:
                break
        order.append(chosen)
        del remaining[chosen]
    return order


def pick_entry(ledger: Ledger, today: date) -> Entry | None:
    """Try each kind in weighted order until one yields an entry."""
    for kind in draw_order(ledger.retired):
        try:
            entry = FETCHERS[kind](ledger, today)
        except Exception as exc:
            print(f"::warning::{kind} raised {exc!r}; trying the next kind.")
            continue
        if entry is not None:
            print(f"picked {entry.commit_type}({entry.scope}): {entry.title}")
            return entry
        print(f"{kind}: nothing available today, trying the next kind.")
    return None
