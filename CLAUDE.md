# The Profile: notes for Claude

Standing rules from the owner, for every session that works on this repository.

## Nothing private is ever named here

This repository is public, and so is everything it publishes: the profile, its commits, the Arbiter's replies on
tannergolden/play and every run's log. No private repository of this account is ever named, linked or described
here: not in a file, a commit message, a pull request's title or description, an issue, a comment, a release note or
a workflow's output.

- Speak of such a repository by its role, never by its name, and read every diff and message for one before it goes
  out.
- Name only the public repositories this one already works with, tannergolden/play, tannergolden/markdown and
  tannergolden/standards, and the public ones the profile itself shows. When you can't tell whether a repository is
  public, leave it out.
- Should a private repository turn up named here, take it out at once and tell the owner. Rewriting history to purge
  it waits for the owner's word.

## The games' licences

- This repository is MIT under [LICENSE](LICENSE), and its scripts carry `SPDX-License-Identifier: MIT`. Change no
  licence here without the owner's word.
- The rest of the games is proprietary, all rights reserved: [tannergolden/play](https://github.com/tannergolden/play)
  under its own LICENSE, and the kit's Game Materials under
  [tannergolden/markdown](https://github.com/tannergolden/markdown)'s LICENSE-GAMES. Copy nothing of theirs in here.

## Moves and their issues

- Every move reaches the games as an issue in tannergolden/play, and the Official Arbiter answers it, labels it
  `played` or `turned away`, files it in its game's milestone and closes it (`.github/scripts/arbiter.sh`).
- Never open, comment on, label or close an issue there, or start a game's workflow, from a test or by hand. The tests
  reach no network: stand-ins only.

## Working here

- The scripts are standard-library Python under `.github/scripts`, with their tests beside them. Run Python with the
  tokens unset, as 🧪 Games Tests runs them:
  `env -u GH_TOKEN -u GITHUB_TOKEN -u MARKDOWN_TOKEN python3 -m unittest discover -s .github/scripts -p 'test_*.py'`,
  with `CHESS_PERFT_DEEP=1` and `CHECKERS_PERFT_DEEP=1` for the deep counts.
- Before a push, a change to the scripts or the games' workflows passes those tests, shellcheck on `arbiter.sh`, and
  actionlint and zizmor on the workflows.
- The kit draws README.md between its `<!-- markdown:...:start -->` and `<!-- markdown:...:end -->` markers, and
  everything under `assets/`: edit only outside them.
- Every folder under `.github/` keeps a README that logs its files. Redraw the logs in the same commit as a change to
  a folder: `python3 <standards>/.github/scripts/update-doc-indexes.py --tree --write`, from tannergolden/standards
  at `v1`.
- A change to how a move is played or answered updates everything that tells it, in the same commits: `docs/README.md`,
  the game's own guide in `docs/`, Play Against Me in README.md, and the header comments of the workflows and of
  `arbiter.sh`.

## Commits

- Conventional Commits with an emoji and a scope, such as `feat(games): 🏷️ close each move's issue with its ruling`: a
  subject under 72 characters, and a body wrapped at 72.
- The author is Tanner Golden <24684994+tannergolden@users.noreply.github.com>, and the last trailer signs it off as
  the owner: `Signed-off-by: Tanner Golden <24684994+tannergolden@users.noreply.github.com>`. The committer stays this
  environment's own, whose key signs the commit.
- Work lands on Development. Never force-push, and never rewrite its history.

## Writing

- No em or en dashes anywhere, chat replies included.
