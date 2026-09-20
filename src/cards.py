# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The two cards on the page, drawn as SVG and committed.

Nothing on the page is fetched from an image service at render time. Both
are drawn from what the GitHub API says about the account's public
repositories. Each comes in a light and a dark variant, and the page switches between them with a
`<picture>` element, because a media query inside an image is honoured by
browsers but not by every proxy in between.

The language card is a chart, so it follows the chart rules: thin bars from
one baseline, a rounded data-end, every bar labelled directly so identity
never rests on colour alone, and the numbers repeated in the image's alt text
as the table view a static image cannot otherwise offer. Colours are each
language's own Linguist colour, which is the convention a reader of GitHub
already carries; the label is what makes them distinguishable, not the hue.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import net
from config import ASSETS_DIR

LINGUIST = "https://raw.githubusercontent.com/github-linguist/linguist/master/lib/linguist/languages.yml"
GRAPHQL = "https://api.github.com/graphql"
API = "https://api.github.com"

# Surfaces and ink from the reference palette, one set per scheme. The dark
# set is its own selection, not an inversion of the light one.
THEMES = {
    "light": {"surface": "#fcfcfb", "border": "#e1e0d9", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781", "track": "#e1e0d9"},
    "dark": {"surface": "#1a1a19", "border": "#383835", "ink": "#ffffff", "ink2": "#c3c2b7", "muted": "#898781", "track": "#2c2c2a"},
}

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

# When the Linguist registry cannot be fetched, the languages this account is
# most likely to show still get their conventional colour.
FALLBACK_COLORS = {
    "Python": "#3572A5", "Shell": "#89e051", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Go": "#00ADD8", "Rust": "#dea584", "Makefile": "#427819", "HTML": "#e34c26", "CSS": "#663399",
    "Dockerfile": "#384d54", "Java": "#b07219", "C": "#555555", "C++": "#f34b7d", "Ruby": "#701516",
    "Jupyter Notebook": "#DA5B0B", "Lua": "#000080", "Swift": "#F05138", "Kotlin": "#A97BFF",
}


def _svg_header(width: int, height: int, title: str, theme: dict) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="t">\n'
        f"<title id=\"t\">{escape(title)}</title>\n"
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" '
        f'fill="{theme["surface"]}" stroke="{theme["border"]}"/>\n'
    )


# --- the account's numbers --------------------------------------------------------

def _headers(token: str | None) -> dict:
    return net.github_headers(token)


def _linguist_colors() -> dict:
    text = net.get_text(LINGUIST)
    if not text:
        return dict(FALLBACK_COLORS)
    colors = dict(FALLBACK_COLORS)
    current = None
    for line in text.splitlines():
        head = re.match(r"^([^\s#][^:]*):\s*$", line)
        if head:
            current = head.group(1).strip().strip('"')
            continue
        color = re.match(r"^\s+color:\s*\"?(#[0-9A-Fa-f]{6})\"?", line)
        if color and current:
            colors[current] = color.group(1)
    return colors


def github_stats(login: str, token: str | None) -> dict | None:
    """Public numbers for the account: repositories, stars, followers, this year's activity, languages."""
    headers = _headers(token)
    user = net.get_json_with_headers(f"{API}/users/{login}", None, headers)
    if not isinstance(user, dict) or "login" not in user:
        return None

    repos: list = []
    for page in range(1, 6):
        batch = net.get_json_with_headers(
            f"{API}/users/{login}/repos", {"per_page": 100, "type": "owner", "page": page}, headers
        )
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(r for r in batch if isinstance(r, dict))
        if len(batch) < 100:
            break

    own = [r for r in repos if not r.get("fork") and not r.get("archived")]
    stars = sum(int(r.get("stargazers_count") or 0) for r in own)
    forks = sum(int(r.get("forks_count") or 0) for r in own)

    languages: dict = {}
    for repo in own:
        url = repo.get("languages_url")
        if not url:
            continue
        found = net.get_json_with_headers(url, None, headers)
        if isinstance(found, dict):
            for name, size in found.items():
                languages[name] = languages.get(name, 0) + int(size or 0)

    year_start = datetime(datetime.now(timezone.utc).year, 1, 1, tzinfo=timezone.utc).isoformat()
    commits = pulls = issues = contributed = None
    if token:
        payload = net.post_json(
            GRAPHQL,
            {
                "query": (
                    "query($login:String!,$from:DateTime!){user(login:$login){"
                    "contributionsCollection(from:$from){totalCommitContributions "
                    "totalPullRequestContributions totalIssueContributions}"
                    "repositoriesContributedTo(first:1,contributionTypes:[COMMIT,PULL_REQUEST,ISSUE]){totalCount}}}"
                ),
                "variables": {"login": login, "from": year_start},
            },
            headers,
        )
        data = (payload or {}).get("data", {}).get("user") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            coll = data.get("contributionsCollection") or {}
            commits = coll.get("totalCommitContributions")
            pulls = coll.get("totalPullRequestContributions")
            issues = coll.get("totalIssueContributions")
            contributed = (data.get("repositoriesContributedTo") or {}).get("totalCount")

    return {
        "login": login,
        "public_repos": int(user.get("public_repos") or 0),
        "followers": int(user.get("followers") or 0),
        "stars": stars,
        "forks": forks,
        "commits": commits,
        "pulls": pulls,
        "issues": issues,
        "contributed": contributed,
        "languages": languages,
        "year": datetime.now(timezone.utc).year,
    }


# --- the two cards ------------------------------------------------------------------

def _fmt(value) -> str:
    if value is None:
        return "n/a"
    value = int(value)
    return f"{value / 1000:.1f}k" if value >= 10_000 else f"{value:,}"


def stats_svg(stats: dict, theme: dict) -> str:
    rows = [
        ("Public repositories", stats["public_repos"]),
        ("Stars earned", stats["stars"]),
        ("Followers", stats["followers"]),
        (f"Commits in {stats['year']}", stats["commits"]),
        (f"Pull requests in {stats['year']}", stats["pulls"]),
        ("Repositories contributed to", stats["contributed"]),
    ]
    width, row_h, top = 400, 26, 52
    height = top + row_h * len(rows) + 14
    out = [_svg_header(width, height, f"GitHub statistics for {stats['login']}", theme)]
    out.append(f'<style>text{{font-family:{SANS}}}</style>')
    out.append(f'<text x="20" y="30" font-size="15" font-weight="600" fill="{theme["ink"]}">{escape(stats["login"])}</text>')
    out.append(f'<text x="{width - 20}" y="30" font-size="11" text-anchor="end" fill="{theme["muted"]}">public activity</text>')
    for index, (label, value) in enumerate(rows):
        y = top + row_h * index + 12
        out.append(f'<text x="20" y="{y}" font-size="13" fill="{theme["ink2"]}">{escape(label)}</text>')
        out.append(f'<text x="{width - 20}" y="{y}" font-size="13" font-weight="600" text-anchor="end" fill="{theme["ink"]}">{escape(_fmt(value))}</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def languages_svg(languages: dict, colors: dict, theme: dict, limit: int = 6) -> str:
    total = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    width, row_h, top_y, bar_x, bar_w, bar_h = 400, 28, 50, 130, 190, 12
    height = top_y + row_h * max(len(top), 1) + 12
    out = [_svg_header(width, height, "Top languages across public repositories", theme)]
    out.append(f'<style>text{{font-family:{SANS}}}</style>')
    out.append(f'<text x="20" y="30" font-size="15" font-weight="600" fill="{theme["ink"]}">Top languages</text>')
    out.append(f'<text x="{width - 20}" y="30" font-size="11" text-anchor="end" fill="{theme["muted"]}">by bytes, public repositories</text>')
    if not top:
        out.append(f'<text x="20" y="{top_y + 14}" font-size="13" fill="{theme["ink2"]}">No language data yet.</text>')
    for index, (name, size) in enumerate(top):
        share = size / total
        y = top_y + row_h * index
        fill = colors.get(name, theme["muted"])
        length = max(4.0, bar_w * share)
        out.append(f'<text x="20" y="{y + 10}" font-size="12" fill="{theme["ink2"]}">{escape(name)}</text>')
        out.append(f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="{bar_h}" rx="4" fill="{theme["track"]}"/>')
        # Rounded at the data end, square at the baseline: a rounded rect with
        # its left corners covered by a short square one.
        out.append(f'<rect x="{bar_x}" y="{y}" width="{length:.1f}" height="{bar_h}" rx="4" fill="{fill}"/>')
        if length > 8:
            out.append(f'<rect x="{bar_x}" y="{y}" width="4" height="{bar_h}" fill="{fill}"/>')
        out.append(f'<text x="{width - 20}" y="{y + 10}" font-size="12" font-weight="600" text-anchor="end" fill="{theme["ink"]}">{share * 100:.1f}%</text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def languages_alt(languages: dict, limit: int = 6) -> str:
    total = sum(languages.values()) or 1
    top = sorted(languages.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    if not top:
        return "Top languages across public repositories: no data yet."
    parts = [f"{name} {size / total * 100:.1f}%" for name, size in top]
    return "Top languages across public repositories: " + ", ".join(parts) + "."


def stats_alt(stats: dict) -> str:
    return (
        f"GitHub statistics for {stats['login']}: {_fmt(stats['public_repos'])} public repositories, "
        f"{_fmt(stats['stars'])} stars, {_fmt(stats['followers'])} followers, "
        f"{_fmt(stats['commits'])} commits and {_fmt(stats['pulls'])} pull requests in {stats['year']}."
    )


# --- writing the files ----------------------------------------------------------------

def _write(path: str, content: str) -> str:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8")
    return path


def content_tag(path: str) -> str:
    """Eight hex characters of the file's hash: the cache-busting query string.

    GitHub's image proxy caches by URL, so a file rewritten at a stable path
    can keep showing its previous contents for hours. A tag derived from the
    bytes changes exactly when the image does and never otherwise.
    """
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:8]
    except OSError:
        return "0"


def write_cards(stats: dict) -> dict:
    colors = _linguist_colors()
    written = {}
    for scheme, theme in THEMES.items():
        written[f"stats-{scheme}"] = _write(f"{ASSETS_DIR}/stats-{scheme}.svg", stats_svg(stats, theme))
        written[f"languages-{scheme}"] = _write(
            f"{ASSETS_DIR}/languages-{scheme}.svg", languages_svg(stats["languages"], colors, theme)
        )
    _write(
        f"{ASSETS_DIR}/cards.json",
        json.dumps({"stats_alt": stats_alt(stats), "languages_alt": languages_alt(stats["languages"])}, indent=2) + "\n",
    )
    return written


def load_card_alts() -> dict:
    try:
        return json.loads(Path(f"{ASSETS_DIR}/cards.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def picture(name: str, alt: str) -> str:
    """A `<picture>` that switches with the reader's colour scheme, cache-busted per file."""
    dark = f"{ASSETS_DIR}/{name}-dark.svg"
    light = f"{ASSETS_DIR}/{name}-light.svg"
    return (
        "<picture>\n"
        f'  <source media="(prefers-color-scheme: dark)" srcset="{dark}?v={content_tag(dark)}">\n'
        f'  <img alt="{escape(alt, {chr(34): "&quot;"})}" src="{light}?v={content_tag(light)}">\n'
        "</picture>"
    )
