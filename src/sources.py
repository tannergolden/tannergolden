# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The five kinds of dispatch, and the picker that chooses between them.

Each fetcher returns one `Dispatch` the ledger has never seen, or None when
its source is down or has nothing new. None is an ordinary answer: the picker
moves to the next kind, and a run in which every source comes back empty writes
nothing and leaves the schedule untouched, so the next run tries again.

Every kind reports something that changed recently. A release from two years
ago is not news, so each fetcher carries a freshness window and returns None
rather than reach back for filler: a quiet week is a quiet page.

Nothing here is hand-written. Every source keeps producing, which is what
lets the ledger promise that no item appears twice without the well ever
running dry.

Every string that leaves a fetcher has been through `text.clean()`.
"""

from __future__ import annotations

import html
import os
import random
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

import net
import phrasing
from config import NEWS_WINDOW_DAYS
from state import Ledger
from text import clean

_RNG = random.SystemRandom()


@dataclass
class Dispatch:
    """One dispatch, ready to be rendered into a commit and a page row."""

    kind: str  # the ledger key and the scope: release, advisory, eol, ...
    commit_type: str  # feat, security, chore, docs
    emoji: str  # one emoji from the house mapping for that type
    subject: str  # lowercase imperative, without the type(scope) prefix
    title: str  # the short form shown in the page's table
    body: str  # prose for the commit body and the archive
    identifier: str  # what the ledger records; unique at the source
    source_name: str
    source_url: str
    license: str  # an SPDX identifier, or a short description when none fits
    attribution: str = ""  # authors or contributors, when the source names them
    extra_links: list = field(default_factory=list)  # (label, url) pairs

    @property
    def scope(self) -> str:
        return self.kind


# --- helpers ----------------------------------------------------------------

def _shuffled(items: list) -> list:
    items = list(items)
    _RNG.shuffle(items)
    return items


# --- feat(release): a new version of a tool people actually run ------------------

GITHUB_API = "https://api.github.com"

# Curated, not scraped. Every entry is a tool a working developer either runs
# or depends on, and every one cuts GitHub releases rather than bare tags, so
# `/releases/latest` answers. A repository that stops publishing releases
# answers 404 and is skipped, which is why the list can go stale safely.
WATCHLIST = (
    ("golang/go", "Go"), ("rust-lang/rust", "Rust"), ("python/cpython", "CPython"),
    ("nodejs/node", "Node.js"), ("denoland/deno", "Deno"), ("oven-sh/bun", "Bun"),
    ("ziglang/zig", "Zig"), ("JuliaLang/julia", "Julia"), ("elixir-lang/elixir", "Elixir"),
    ("microsoft/TypeScript", "TypeScript"), ("llvm/llvm-project", "LLVM"),
    ("kubernetes/kubernetes", "Kubernetes"), ("moby/moby", "Docker Engine"),
    ("docker/compose", "Docker Compose"), ("hashicorp/terraform", "Terraform"),
    ("etcd-io/etcd", "etcd"), ("grafana/grafana", "Grafana"),
    ("prometheus/prometheus", "Prometheus"), ("redis/redis", "Redis"),
    ("valkey-io/valkey", "Valkey"), ("duckdb/duckdb", "DuckDB"),
    ("elastic/elasticsearch", "Elasticsearch"), ("apache/kafka", "Kafka"),
    ("neovim/neovim", "Neovim"), ("helix-editor/helix", "Helix"), ("zed-industries/zed", "Zed"),
    ("astral-sh/ruff", "Ruff"), ("astral-sh/uv", "uv"), ("psf/black", "Black"),
    ("pytest-dev/pytest", "pytest"), ("vitejs/vite", "Vite"), ("pnpm/pnpm", "pnpm"),
    ("facebook/react", "React"), ("vuejs/core", "Vue"), ("sveltejs/svelte", "Svelte"),
    ("angular/angular", "Angular"), ("denoland/fresh", "Fresh"),
    ("rails/rails", "Rails"), ("django/django", "Django"), ("fastapi/fastapi", "FastAPI"),
    ("pallets/flask", "Flask"), ("spring-projects/spring-boot", "Spring Boot"),
    ("pytorch/pytorch", "PyTorch"), ("huggingface/transformers", "Transformers"),
    ("ollama/ollama", "Ollama"), ("ggml-org/llama.cpp", "llama.cpp"),
    ("curl/curl", "curl"), ("openssl/openssl", "OpenSSL"),
    ("caddyserver/caddy", "Caddy"), ("traefik/traefik", "Traefik"),
    ("cli/cli", "GitHub CLI"), ("jqlang/jq", "jq"), ("BurntSushi/ripgrep", "ripgrep"),
    ("sharkdp/fd", "fd"), ("starship/starship", "Starship"), ("tmux/tmux", "tmux"),
)

# Release notes are Markdown written by whoever cut the release, so the first
# paragraph is taken and the rest dropped.
HEADLINE = re.compile(r"^\s*(?:#{1,6}\s*)?(?P<line>[^\n#*\-][^\n]{20,})", re.MULTILINE)


def _fresh(stamp: str, days: int = NEWS_WINDOW_DAYS) -> bool:
    """True when an ISO timestamp is inside the window that still counts as news."""
    try:
        when = datetime.fromisoformat(clean(stamp).replace("Z", "+00:00"))
    except ValueError:
        return False
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    return timedelta(0) <= datetime.now(timezone.utc) - when <= timedelta(days=days)


def _age(stamp: str) -> str:
    when = datetime.fromisoformat(clean(stamp).replace("Z", "+00:00"))
    days = (datetime.now(timezone.utc) - when).days
    return "today" if days < 1 else ("yesterday" if days == 1 else f"{days} days ago")


def fetch_release(ledger: Ledger, today: date) -> Dispatch | None:
    headers = net.github_headers(os.environ.get("GITHUB_TOKEN"))
    for repo, product in _shuffled(list(WATCHLIST))[:8]:
        release = net.get_json_with_headers(f"{GITHUB_API}/repos/{repo}/releases/latest", None, headers)
        if not isinstance(release, dict) or release.get("draft") or release.get("prerelease"):
            continue
        tag = clean(str(release.get("tag_name") or ""))
        published = str(release.get("published_at") or "")
        if not tag or not _fresh(published) or ledger.seen("release", f"{repo}@{tag}"):
            continue

        version = tag.lstrip("vV") if tag[:1] in "vV" and tag[1:2].isdigit() else tag
        headline = HEADLINE.search(clean(str(release.get("body") or ""), allow_newlines=True))
        body = phrasing.one_of(
            f"{product} {version} was published {_age(published)}.",
            f"{product} cut {version} {_age(published)}.",
            f"A new {product}: {version}, {_age(published)}.",
        )
        if headline:
            note = clean(headline.group("line"))
            body += " " + (note if len(note) <= 300 else note[:299].rsplit(" ", 1)[0] + "\u2026")
        return Dispatch(
            kind="release",
            commit_type="feat",
            emoji=phrasing.emoji_for("feat"),
            subject=f"{phrasing.verb_for('release')} {product} {version}",
            title=f"{product} {version}",
            body=body,
            identifier=f"{repo}@{tag}",
            source_name=repo,
            source_url=str(release.get("html_url") or f"https://github.com/{repo}/releases"),
            license="Release metadata, reported as fact",
        )
    return None


# --- security(advisory): something to patch this week ----------------------------

ADVISORIES = f"{GITHUB_API}/advisories"


def fetch_advisory(ledger: Ledger, today: date) -> Dispatch | None:
    headers = net.github_headers(os.environ.get("GITHUB_TOKEN"))
    severity = phrasing.one_of("critical", "critical", "high")
    found = net.get_json_with_headers(
        ADVISORIES,
        {"type": "reviewed", "severity": severity, "sort": "published", "direction": "desc", "per_page": 50},
        headers,
    )
    if not isinstance(found, list):
        return None

    for item in _shuffled([a for a in found if isinstance(a, dict)]):
        ghsa = clean(str(item.get("ghsa_id") or ""))
        published = str(item.get("published_at") or "")
        if not ghsa or not _fresh(published) or ledger.seen("advisory", ghsa):
            continue
        affected = [v for v in (item.get("vulnerabilities") or []) if isinstance(v, dict)]
        package = ""
        ecosystem = ""
        versions = ""
        if affected:
            named = (affected[0].get("package") or {}) if isinstance(affected[0].get("package"), dict) else {}
            package = clean(str(named.get("name") or ""))
            ecosystem = clean(str(named.get("ecosystem") or ""))
            versions = clean(str(affected[0].get("vulnerable_version_range") or ""))
        summary = clean(str(item.get("summary") or ""))
        cve = clean(str(item.get("cve_id") or ""))

        where = f"{package} ({ecosystem})" if package and ecosystem else (package or "a reviewed package")
        body = phrasing.one_of(
            f"{severity.capitalize()} severity in {where}, published {_age(published)}.",
            f"Published {_age(published)}: a {severity} severity advisory against {where}.",
            f"{where} carries a {severity} severity advisory, {_age(published)}.",
        )
        if summary:
            body += f" {summary}" + ("" if summary.endswith(".") else ".")
        if versions:
            body += f" Affected: {versions}."
        if cve:
            body += f" Tracked as {cve}."
        return Dispatch(
            kind="advisory",
            commit_type="security",
            emoji=phrasing.emoji_for("security"),
            subject=f"{phrasing.verb_for('advisory')} the {severity} advisory in {package or ghsa}",
            title=f"{ghsa}: {package or 'a reviewed package'}",
            body=body,
            identifier=ghsa,
            source_name="GitHub Security Advisories",
            source_url=str(item.get("html_url") or f"https://github.com/advisories/{ghsa}"),
            license="Advisory metadata, reported as fact",
        )
    return None


# --- chore(eol): a version that stops getting fixes --------------------------------

EOL_ALL = "https://endoflife.date/api/all.json"
EOL_PRODUCT = "https://endoflife.date/api/{product}.json"


def _eol_cycles(payload) -> list:
    """The cycle records, whichever shape the API answers.

    The long-lived endpoint returns a bare array of cycles. The newer one
    wraps them in {"result": {"releases": [...]}}, so both are unwrapped here
    rather than pinning a version of somebody else's API.
    """
    if isinstance(payload, dict):
        payload = (payload.get("result") or {}).get("releases", payload.get("releases"))
    return [c for c in (payload or []) if isinstance(c, dict)] if isinstance(payload, list) else []


def fetch_eol(ledger: Ledger, today: date) -> Dispatch | None:
    products = net.get_json(EOL_ALL)
    names = [clean(str(p)) for p in products if isinstance(p, str)] if isinstance(products, list) else []
    if not names:
        return None

    for product in _shuffled(names)[:10]:
        cycles = _eol_cycles(net.get_json(EOL_PRODUCT.format(product=urllib.parse.quote(product, safe=""))))
        for cycle in cycles:
            eol = cycle.get("eol") if not isinstance(cycle.get("eol"), bool) else None
            name = clean(str(cycle.get("cycle") or cycle.get("name") or ""))
            if not eol or not name:
                continue
            try:
                when = date.fromisoformat(clean(str(eol)))
            except ValueError:
                continue
            days = (when - today).days
            # A window either side: what is about to stop getting fixes, and
            # what just did. Anything further out is a calendar entry.
            if not -NEWS_WINDOW_DAYS <= days <= 90 or ledger.seen("eol", f"{product}-{name}"):
                continue

            label = product.replace("-", " ").title()
            latest = clean(str(cycle.get("latest") or ""))
            timing = (
                "reaches end of life today" if days == 0
                else (f"reaches end of life in {days} days" if days > 0 else f"reached end of life {-days} days ago")
            )
            body = phrasing.one_of(
                f"{label} {name} {timing}.",
                f"{timing.capitalize()}: {label} {name}.",
                f"{label} {name}, and it {timing}.",
            )
            body += f" The last release on that line was {latest}." if latest else ""
            body += " After that date it stops receiving fixes, security ones included."
            return Dispatch(
                kind="eol",
                commit_type="chore",
                emoji=phrasing.emoji_for("chore"),
                subject=f"{phrasing.verb_for('eol')} {label} {name} at end of life",
                title=f"{label} {name}, {timing}",
                body=body,
                identifier=f"{product}-{name}",
                source_name="endoflife.date",
                source_url=f"https://endoflife.date/{product}",
                license="CC-BY-4.0",
            )
    return None


# --- docs(rfc): a standard published this year ----------------------------------------

RFC_JSON = "https://www.rfc-editor.org/rfc/rfc{n}.json"
RFC_PAGE = "https://www.rfc-editor.org/rfc/rfc{n}"

# Where the series had reached when this was written. A number past the end
# answers 404, which walks the working ceiling down, so the constant going
# stale costs one wasted request rather than a broken kind.
RFC_CEILING = 9820
RFC_RECENT = 250


def _html_to_text(value: str) -> str:
    """The RFC Editor's abstracts arrive as HTML paragraphs; keep the breaks, drop the tags."""
    text = re.sub(r"</p>\s*<p[^>]*>", "\n\n", value, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return html.unescape(text)


def fetch_rfc(ledger: Ledger, today: date) -> Dispatch | None:
    ceiling = RFC_CEILING
    for _ in range(10):
        n = _RNG.randint(max(ceiling - RFC_RECENT, 1), ceiling)
        if ledger.seen("rfc", str(n)):
            continue
        meta = net.get_json(RFC_JSON.format(n=n))
        if not isinstance(meta, dict) or not meta.get("title"):
            # Past the end of the series, or never issued. Walk down.
            ceiling = max(n - 1, 1)
            continue
        title = clean(str(meta.get("title", "")))
        published = clean(str(meta.get("pub_date", "") or ""))
        if title.lower() in ("not issued", "") or not published:
            continue
        year = re.search(r"\b(\d{4})\b", published)
        if not year or today.year - int(year.group(1)) > 2:
            continue

        status = clean(str(meta.get("status", "") or "")).lower()
        abstract = clean(_html_to_text(str(meta.get("abstract", "") or "")), allow_newlines=True)
        authors = ", ".join(clean(str(a)) for a in (meta.get("authors") or []) if a)
        body = phrasing.one_of(
            f"Published in {published}" + (f", with the status {status}." if status else "."),
            f"{published}" + (f", status {status}." if status else "."),
            f"The series reached this one in {published}" + (f", as {status}." if status else "."),
        )
        if abstract:
            body += "\n\n" + abstract
        return Dispatch(
            kind="rfc",
            commit_type="docs",
            emoji=phrasing.emoji_for("docs"),
            subject=f"{phrasing.verb_for('rfc')} RFC {n}, {title}",
            title=f"RFC {n}: {title}",
            body=body,
            identifier=str(n),
            source_name="RFC Editor",
            source_url=RFC_PAGE.format(n=n),
            license="IETF Trust Legal Provisions; RFCs may be freely reproduced",
            attribution=authors,
        )
    return None


# --- docs(lobsters): what the quiet end of the internet is reading ----------------------

LOBSTERS = "https://lobste.rs/hottest.json"
LOBSTERS_FLOOR = 15


def fetch_lobsters(ledger: Ledger, today: date) -> Dispatch | None:
    stories = net.get_json(LOBSTERS)
    if not isinstance(stories, list):
        return None
    for story in _shuffled([s for s in stories if isinstance(s, dict)]):
        short_id = clean(str(story.get("short_id") or ""))
        score = int(story.get("score") or 0)
        url = str(story.get("url") or "")
        comments = str(story.get("comments_url") or "")
        if not short_id or score < LOBSTERS_FLOOR or ledger.seen("lobsters", short_id):
            continue
        if not url.startswith("https://"):
            url = comments if comments.startswith("https://") else ""
        if not url:
            continue

        title = clean(str(story.get("title") or ""))
        tags = [clean(str(t)) for t in (story.get("tags") or []) if t]
        domain = urllib.parse.urlsplit(url).netloc.lower().removeprefix("www.")
        submitter = clean(str((story.get("submitter_user") or {}).get("username") or "")) if isinstance(story.get("submitter_user"), dict) else clean(str(story.get("submitter_user") or ""))
        body = phrasing.one_of(
            f"{score} points on Lobsters, from {domain}.",
            f"From {domain}, sitting at {score} points on Lobsters.",
            f"Lobsters has it at {score} points; the source is {domain}.",
        )
        if tags:
            body += " Tagged " + ", ".join(tags[:4]) + "."
        return Dispatch(
            kind="lobsters",
            commit_type="docs",
            emoji=phrasing.emoji_for("docs"),
            subject=f"{phrasing.verb_for('lobsters')} {title}",
            title=title,
            body=body,
            identifier=short_id,
            source_name="Lobsters",
            source_url=url,
            license="Title and score, reported as fact",
            attribution=f"submitted by {submitter}" if submitter else "",
            extra_links=[("discussion", comments)] if comments.startswith("https://") else [],
        )
    return None


# --- the picker -------------------------------------------------------------------

FETCHERS: dict = {
    "release": fetch_release,
    "advisory": fetch_advisory,
    "eol": fetch_eol,
    "rfc": fetch_rfc,
    "lobsters": fetch_lobsters,
}

KINDS = ("release", "advisory", "eol", "rfc", "lobsters")


def draw_order() -> list:
    """The kinds in the order they will be tried.

    An earlier design weighted this, because two kinds drew on finite lists
    that had to be rationed. Every source here keeps producing, so the five
    are equals and the order is a plain shuffle.
    """
    return _shuffled(list(KINDS))


def pick_dispatch(ledger: Ledger, today: date) -> Dispatch | None:
    """Try each kind in turn until one yields an entry."""
    for kind in draw_order():
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
