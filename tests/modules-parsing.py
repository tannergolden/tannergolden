# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The terminal tip and the stats fetch, against recorded API shapes.

TAR_PAGE is the tldr format as it is actually written today: a heading that
is the real command, a summary block ending in a "More information" line,
mnemonic brackets in the descriptions, and placeholders that sometimes offer
a short and a long spelling of one flag.
"""

from __future__ import annotations

import cards
import modules
from state import Ledger

TAR_PAGE = """# tar

> Archiving utility.
> Often combined with a compression method, such as `gzip`.
> More information: <https://www.gnu.org/software/tar>.

- [c]reate an archive and write it to a [f]ile:

`tar cf {{path/to/target.tar}} {{path/to/file1 path/to/file2 ...}}`

- E[x]tract a (compressed) archive [f]ile into the target directory:

`tar xf {{path/to/source.tar.ext}} {{[-C|--directory]}} {{path/to/directory}}`

- [l]ist the contents of a tar [f]ile [v]erbosely \u2014 with a dash:

`tar tvf {{path/to/source.tar}}`

- [c]reate a g[z]ipped archive, e[x]cluding a pattern:

`tar czf {{path/to/target.tar.gz}} --exclude {{pattern}} {{path/to/directory}}`

- [c]reate an archive from a directory using relative paths:

`tar czf {{path/to/target.tar.gz}} {{[-C|--directory]}} {{path/to/directory}} .`
"""

# Four examples, only one of which carries a flag: below the floor at which
# preferring them would stop being a preference.
FLAT_PAGE = """# flat

> A tool whose examples are mostly bare.
> More information: <https://example.invalid>.

- Do the first thing:

`flat {{path/to/file}}`

- Do the second thing:

`flat {{path/to/other}}`

- Do the third thing:

`flat {{path/to/third}}`

- Do it verbosely:

`flat --verbose {{path/to/file}}`
"""

THIN_PAGE = """# thin

> A tool that does one thing.
> More information: <https://example.invalid>.

- Do the one thing:

`thin {{path/to/file}}`
"""

SSH_PAGE = """# ssh

> Secure Shell is a protocol used to securely log onto remote systems.
> More information: <https://man.openbsd.org/ssh>.

- Connect with a specific identity:

`ssh {{username}}@{{remote_host}} -i {{path/to/key_file}}`

- Connect on a specific port:

`ssh {{username}}@{{remote_host}} -p {{2222}}`

- Run a command remotely:

`ssh {{username}}@{{remote_host}} {{command}}`
"""


def tree(*names):
    return {"tree": [{"path": f"{n}.md"} for n in names] + [{"path": "not-a-page.txt"}]}


def page_url(name):
    return modules.TLDR_PAGE.format(name=name)


def tip(fake_net, name, body, *, listed=None):
    fake_net.json(modules.TLDR_TREE, tree(*(listed or [name])))
    fake_net.text(page_url(name), body)
    return modules.terminal_tip(Ledger("state/ledger.json"))


def test_the_heading_is_the_command_not_the_file_name(repo, fake_net, seeded):
    """`git-bisect` is a slug. `git bisect` is what somebody types."""
    fake_net.json(modules.TLDR_TREE, tree("git-bisect"))
    fake_net.text(page_url("git-bisect"), TAR_PAGE.replace("# tar", "# git bisect"))
    found = modules.terminal_tip(Ledger("state/ledger.json"))
    assert found["command"] == "git bisect"
    assert found["id"] == "git-bisect" and found["url"].endswith("/pages/common/git-bisect.md")


def test_the_tip_carries_what_the_tool_is_as_well_as_what_the_line_does(repo, fake_net, seeded):
    found = tip(fake_net, "tar", TAR_PAGE)
    assert found["summary"] == "Archiving utility."  # not the "More information" line
    assert found["description"] and found["description"] != found["summary"]


def test_mnemonic_brackets_become_prose_and_keep_the_capital(repo, fake_net, seeded):
    """"E[x]tract a [f]ile" is terminal shorthand; on a page it is bracket noise."""
    for _ in range(20):
        found = tip(fake_net, "tar", TAR_PAGE)
        if found is None:
            continue
        assert "[" not in found["description"] and "]" not in found["description"]
        assert found["description"][:1].isupper(), found["description"]
        assert "\u2014" not in found["description"]


def test_a_flag_placeholder_resolves_to_the_long_spelling(repo, fake_net, seeded):
    """{{[-C|--directory]}} is two spellings of one flag. The long one explains itself."""
    seen = set()
    for _ in range(40):
        found = tip(fake_net, "tar", TAR_PAGE)
        if found:
            seen.add(found["example"])
    joined = " ".join(seen)
    assert "--directory" in joined and "[-C|--directory]" not in joined
    assert "{{" not in joined and "}}" not in joined


def test_a_placeholder_becomes_something_a_reader_can_fill_in(repo, fake_net, seeded):
    seen = {tip(fake_net, "tar", TAR_PAGE)["example"] for _ in range(40)}
    assert any("<path/to/" in e for e in seen), seen


def test_an_at_sign_in_a_command_survives(repo, fake_net, seeded):
    """user@host is not a mention, and a fullwidth twin would break the line."""
    for _ in range(20):
        found = tip(fake_net, "ssh", SSH_PAGE)
        if found:
            assert "<username>@<remote_host>" in found["example"], found["example"]
            assert "\uff20" not in found["example"]


def test_the_examples_that_show_a_flag_are_preferred(repo, fake_net, seeded):
    """A bare `tar cf x y` shows the tool exists. The rest show how it is driven."""
    assert len(modules.EXAMPLE.findall(TAR_PAGE)) == 5
    seen = {tip(fake_net, "tar", TAR_PAGE)["example"] for _ in range(60)}
    assert len(seen) == 3, seen  # the three that carry one, and no others
    assert all("--" in e for e in seen), seen


def test_the_preference_yields_on_a_page_that_cannot_afford_it(repo, fake_net, seeded):
    """With one flagged example, preferring it would pin the page to that line.

    The point of the pools is that a command shown twice reads differently.
    A filter that leaves one candidate defeats it, so below the floor every
    example is back in the draw.
    """
    seen = {tip(fake_net, "flat", FLAT_PAGE)["example"] for _ in range(60)}
    assert len(seen) == 4, seen


def test_a_page_with_too_few_examples_is_not_drawn(repo, fake_net, seeded):
    """One example is a single-purpose tool, and its tip teaches a name."""
    assert tip(fake_net, "thin", THIN_PAGE) is None


def test_a_command_is_never_shown_twice(repo, fake_net, seeded):
    led = Ledger("state/ledger.json")
    fake_net.json(modules.TLDR_TREE, tree("tar"))
    fake_net.text(page_url("tar"), TAR_PAGE)
    assert modules.terminal_tip(led)["id"] == "tar"
    assert modules.terminal_tip(led) is None


def test_terminal_tip_falls_back_to_the_contents_listing(repo, fake_net, seeded):
    fake_net.json(modules.TLDR_TREE, {"message": "Not Found"})
    fake_net.json(modules.TLDR_LIST, [{"name": "tar.md", "type": "file"}])
    fake_net.text(page_url("tar"), TAR_PAGE)
    assert modules.terminal_tip(Ledger("state/ledger.json"))["command"] == "tar"


def test_a_source_that_is_down_answers_none(repo, fake_net, seeded):
    assert modules.terminal_tip(Ledger("state/ledger.json")) is None


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
