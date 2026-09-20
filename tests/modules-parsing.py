# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The three daily modules and the stats fetch, against recorded API shapes."""

from __future__ import annotations

import cards
import modules
from state import Ledger

JQ_PAGE = """# jq

> A JSON processor that uses a domain-specific language (DSL).
> More information: <https://jqlang.org/manual/>.

- Execute a specific expression only using the `jq` binary (print a colored and formatted JSON output):

`jq '.' {{path/to/file.json}}`

- Print a specific key \u2014 with a dash:

`jq '.{{key_name}}' {{path/to/file.json}}`
"""


def test_show_hn_strips_the_prefix_and_skips_what_it_has_shown(repo, fake_net, seeded):
    fake_net.json(modules.HN_SHOW, [11, 12]).json(
        "https://hacker-news.firebaseio.com/v0/item/11.json",
        {"type": "story", "title": "Show HN: Foo \u2013 a thing", "url": "https://www.foo.example/x?y", "score": 42},
    ).json("https://hacker-news.firebaseio.com/v0/item/12.json", {"type": "story", "title": "Show HN: Bar", "score": 3})
    led = Ledger("state/ledger.json")
    led.remember("hn", "11")
    found = modules.show_hn(led)
    assert found == {
        "id": "12", "title": "Bar", "url": "https://news.ycombinator.com/item?id=12", "points": 3,
        "domain": "news.ycombinator.com", "discussion": "https://news.ycombinator.com/item?id=12",
    }
    led2 = Ledger("state/ledger.json")
    first = modules.show_hn(led2)
    assert first["title"] == "Foo - a thing" and first["domain"] == "foo.example"


def test_good_first_issue_filters_to_real_issues_on_github(repo, fake_net, seeded, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    fake_net.json(modules.GITHUB_SEARCH, {"items": [
        {"html_url": "https://github.com/o/r/pull/1", "title": "a pull request", "pull_request": {}},
        {"html_url": "https://github.com/o/r/issues/5", "title": "Fix the | thing"},
    ]})
    found = modules.good_first_issue(Ledger("state/ledger.json"), ["Python"])
    assert found == {"id": "https://github.com/o/r/issues/5", "repo": "o/r", "number": 5, "title": "Fix the | thing", "url": "https://github.com/o/r/issues/5", "language": "Python"}
    assert 'label%3A%22good+first+issue%22' in fake_net.requests[0] and "language%3A%22Python%22" in fake_net.requests[0]
    assert modules.good_first_issue(Ledger("state/ledger.json"), []) is None


def test_terminal_tip_reads_the_tree_and_one_example(repo, fake_net, seeded):
    fake_net.json(modules.TLDR_TREE, {"tree": [{"path": "jq.md"}, {"path": "not-a-page.txt"}]})
    fake_net.text("https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/jq.md", JQ_PAGE)
    found = modules.terminal_tip(Ledger("state/ledger.json"))
    assert found["command"] == "jq" and found["url"].endswith("/pages/common/jq.md")
    assert found["example"] in ("jq '.' <path/to/file.json>", "jq '.<key_name>' <path/to/file.json>")
    assert found["description"] in ("Execute a specific expression only using the `jq` binary (print a colored and formatted JSON output)", "Print a specific key - with a dash")


def test_terminal_tip_falls_back_to_the_contents_listing(repo, fake_net, seeded):
    fake_net.json(modules.TLDR_TREE, {"message": "Not Found"})
    fake_net.json(modules.TLDR_LIST, [{"name": "jq.md", "type": "file"}])
    fake_net.text("https://raw.githubusercontent.com/tldr-pages/tldr/main/pages/common/jq.md", JQ_PAGE)
    assert modules.terminal_tip(Ledger("state/ledger.json"))["command"] == "jq"


def test_github_stats_sums_public_repositories(repo, fake_net):
    fake_net.json("https://api.github.com/users/someone/repos", [
        {"fork": False, "archived": False, "stargazers_count": 3, "forks_count": 1, "languages_url": "https://api.github.com/repos/someone/a/languages"},
        {"fork": True, "archived": False, "stargazers_count": 99, "forks_count": 9, "languages_url": "https://api.github.com/repos/someone/fork/languages"},
    ]).json("https://api.github.com/users/someone", {"login": "someone", "public_repos": 2, "followers": 12})
    fake_net.json("https://api.github.com/repos/someone/a/languages", {"Python": 1000, "Shell": 200})
    fake_net.json(cards.GRAPHQL, {"data": {"user": {"contributionsCollection": {"totalCommitContributions": 412, "totalPullRequestContributions": 58, "totalIssueContributions": 9}, "repositoriesContributedTo": {"totalCount": 6}}}})
    stats = cards.github_stats("someone", "token")
    assert stats["stars"] == 3 and stats["forks"] == 1 and stats["followers"] == 12
    assert stats["languages"] == {"Python": 1000, "Shell": 200}
    assert stats["commits"] == 412 and stats["pulls"] == 58 and stats["contributed"] == 6
    assert cards.stats_alt(stats).startswith("GitHub statistics for someone: 2 public repositories, 3 stars, 12 followers, 412 commits")
    assert cards.languages_alt(stats["languages"]) == "Top languages across public repositories: Python 83.3%, Shell 16.7%."


def test_github_stats_without_a_token_leaves_the_year_unknown(repo, fake_net):
    fake_net.json("https://api.github.com/users/someone/repos", []).json("https://api.github.com/users/someone", {"login": "someone", "public_repos": 0, "followers": 0})
    stats = cards.github_stats("someone", None)
    assert stats["commits"] is None and cards.GRAPHQL not in fake_net.requests
    assert cards.github_stats("nobody", None) is None
