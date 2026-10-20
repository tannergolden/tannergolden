<!--
title: '⏰ WORKFLOWS & SCHEDULES'
description: 'Every workflow on the profile at a glance: what starts it and when, in UTC and EST, what it may write, the secrets and tokens it reads, the commits it makes and how it keeps out of another run''s way. Consult it when a run is due, late, or asks for a secret.'
type: reference
keywords: [github-actions, cron, permissions, secrets, tokens, commits, concurrency]
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# ⏰ WORKFLOWS & SCHEDULES

<a name="top"></a>

**Every run on the profile: when it comes, what it may touch, and what it commits.**

_Each weekly run keeps a day of its own._

</div>

---

## ⏰ The Schedules

The page tells time in EST, UTC-5, and never moves to daylight time, so each
EST time below holds all year round.

| Workflow                                      | Cron, in UTC                 | In EST                          | Does                                                                                    |
| :-------------------------------------------- | :--------------------------- | :------------------------------ | :-------------------------------------------------------------------------------------- |
| ⏰ Clock, `clock.yml`                         | `17,47 * * * *`              | Twice an hour, at :17 and :47   | Every game's Arbiter, in one run                                                        |
| 📝 Markdown, `markdown.yml`                   | `0 5 * * *`                  | Every day at 00:00              | Draws the whole page                                                                    |
| 📝 Notes, `notes.yml`                         | `30 14 * * 1`                | Mondays at 09:30                | Redraws the Field Notes                                                                 |
| 📌 Picks, `picks.yml`                         | `30 14 * * 3`, `30 14 * * 5` | Wednesdays and Fridays at 09:30 | Picks the latest releases, then the good first issues                                   |
| Dependabot, `dependabot.yml`                  | monthly, at 07:00 UTC        | Monthly, at 02:00               | One pull request updating every pinned action                                           |
| 🔁 Intelligence Sync, `intelligence-sync.yml` | `23 6 * * 1`                 | Mondays at 01:23                | One pull request with the hub's latest universal rules for AI agents, when they changed |

- **The clock runs off the hour**, since GitHub delays scheduled runs at the
  top of the hour and drops some; each tick catches up on whatever the one
  before it missed.
- **Each weekly run has a day of its own**, at an hour well clear of the
  Markdown run at midnight, so no two of them push at once. 🔁 Intelligence
  Sync shares Monday with the Field Notes, but it pushes only its own branch,
  `chore/intelligence`, and never Development.
- **Every workflow but `game.yml` can also be run by hand.** Never start a
  game's workflow that way: every move reaches it as an issue in
  tannergolden/play, and a run with no issue is accepted only from the owner,
  as their own move.

---

## 🚀 What Starts Each Run, And What It Writes

| Workflow                                    | Started by                                                                        | Writes                                                                                      | Starts                                                         |
| :------------------------------------------ | :-------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------ | :------------------------------------------------------------- |
| `chess.yml`                                 | play's Move Intake, through the Official Arbiter                                  | `.github/chess/`, and the `chess` and `hall` regions                                        | 📝 Markdown; play's `replay.yml` after a person's winning move |
| `tictac.yml`, `pentago.yml`, `checkers.yml` | the same; each calls `game.yml` with its game's key                               | `.github/<game>/`, and its region and `hall`                                                | the same                                                       |
| `game.yml`                                  | those three, as a reusable workflow                                               | as its caller                                                                               | as its caller                                                  |
| `clock.yml`                                 | its schedule, or by hand                                                          | every game's folder, every game's region and `hall`                                         | 📝 Markdown, when anything changed                             |
| `markdown.yml`                              | its schedule, Picks, the games, the clock, or by hand                             | the README's kit blocks, `assets/` and the lock                                             | nothing                                                        |
| `notes.yml`                                 | its schedule, or by hand                                                          | the README's Field Notes block                                                              | nothing                                                        |
| `picks.yml`                                 | its schedules, or by hand, which picks both                                       | the `releases` and `issues` regions                                                         | 📝 Markdown, when either moved                                 |
| `games-tests.yml`                           | a push that changes the scripts, `arbiter.sh` or the games' workflows, or by hand | nothing                                                                                     | nothing                                                        |
| `intelligence-sync.yml`                     | its schedule, or by hand                                                          | `AGENTS.md`, on the `chore/intelligence` branch, as one pull request for the owner to merge | nothing                                                        |

🧪 Games Tests watches `.github/scripts/*.py`, `.github/scripts/arbiter.sh`,
the four games' workflows, `game.yml`, `clock.yml` and itself. A move's own
commit touches only the games' state and the settings, so it never starts it.

---

## 🛡️ Permissions & Secrets

Every workflow grants nothing at the top, `permissions: {}`, and each job only
what it needs. Third-party actions are pinned to a commit, with their version
in a comment, and Dependabot proposes their updates once a month; the kit's
workflow is called at its moving major tag, `@v1`, and tannergolden/intelligence's
at its own, `@v0`.

| Workflow                                   | The job may                               | For                                                                                                              |
| :----------------------------------------- | :---------------------------------------- | :--------------------------------------------------------------------------------------------------------------- |
| `chess.yml`, and `game.yml` for the others | `actions: write`, `contents: write`       | Starting the Markdown run; the game's state and the settings                                                     |
| `clock.yml`                                | `actions: write`, `contents: write`       | The same, for every game                                                                                         |
| `markdown.yml`                             | `contents: write`, `pull-requests: write` | The images, the README's blocks and the lock; pull requests only with `commit: pr`, which this stub does not set |
| `notes.yml`                                | `contents: write`                         | The README's block                                                                                               |
| `picks.yml`                                | `actions: write`, `contents: write`       | The placards' lines, and starting the Markdown run                                                               |
| `games-tests.yml`                          | `contents: read`                          | The code under test, checked out without credentials                                                             |
| `intelligence-sync.yml`                    | `contents: write`, `pull-requests: write` | Pushing `chore/intelligence`, and opening or updating its one pull request                                       |

| Name                   | Kind                 | Read by                                                             | For                                                                                                                                                              |
| :--------------------- | :------------------- | :------------------------------------------------------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PLAY_APP_CLIENT_ID`   | variable             | `chess.yml`, `game.yml`, `clock.yml`                                | The Official Arbiter App's Client ID                                                                                                                             |
| `PLAY_APP_PRIVATE_KEY` | secret               | the same, the three games' workflows passing it to `game.yml`       | The App's private key                                                                                                                                            |
| `BOT_ACCESS_TOKEN`     | secret, optional     | `intelligence-sync.yml`, which hands it to the hub's workflow alone | Opening the sync pull request as the owner; without it, the run's own token opens it, and Actions must be allowed to create pull requests                        |
| `MARKDOWN_TOKEN`       | secret, optional     | `markdown.yml`, which hands it to the kit alone                     | The kit's reads of GitHub; without it, the kit reads with the run's own token                                                                                    |
| `GITHUB_TOKEN`         | each run's own token | every workflow that pushes or reads GitHub                          | Pushing; reading a move's issue on play; starting the Markdown run; the Advisory Database for the Field Notes; GitHub's API, search and GraphQL for the placards |

From the App's two credentials, each run mints tokens that reach
tannergolden/play alone: Issues write for the replies, the rulings and the
notices, and Actions write to ask play's Replay workflow for a replay. Without
the two, a move is still played, but its reply and its ruling fail, and so do
the clock's notices. Setting the App up, and rotating its key, are in play's
[GitHub App](https://github.com/tannergolden/play/blob/Development/docs/operations/GitHub-App.md)
guide; what the kit does with `MARKDOWN_TOKEN` is in the kit's
[One Stub](https://github.com/tannergolden/markdown#-one-stub).

---

## 🌿 The Commits

The games, the clock, Notes and Picks commit as `github-actions[bot]`, so a
move never counts as anyone's contribution, and no message of theirs names an
issue, since a reference in a commit message would land on that issue's
timeline. A move's commit body says `Move <M>, by <login>.`, and each of their
commits names the run that made it. The kit makes its own commit, as its
README shows.

| Commit                             | Message                                                                                                                                                     |
| :--------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A move                             | `chore(<game>): <sign> play <move> in game <N>`                                                                                                             |
| A move that ends a game            | `chore(chess): 🏆 play <move>, ending game <N> <result>`; in the others, `chore(<game>): 🏆 play <move>, ending game <N>: <side> wins`, or `🤝` and `drawn` |
| A ghost                            | `chore(<game>): 👻 place <ghost> for <side> in game <N>` (`set` in Pentago), the second adding `, drawing <side> to open`                                   |
| The Arbiter's week                 | `chore(<game>): ⏰ play <move> for <side> after a week without a move`; for a ghost, `👻 ... after a week without one`                                      |
| A fresh board's draw               | `chore(<game>): 🎲 start game <N>, <side> to place the first ghost` (`set` in Pentago)                                                                      |
| Checkers' first game               | `chore(checkers): 🏁 start game 1, GitHub to open as Black`                                                                                                 |
| A tick that moved several games    | `chore(games): ⏰ run the clock for <the games>`, with each game's own message in its body                                                                  |
| Boards set out again, with no move | `chore(<game>): 🖌️ set the board out for the page`; from the clock, `chore(games): 🖌️ set the boards out for the page`                                      |
| The Field Notes                    | `chore(notes): 📝 redraw the field notes`                                                                                                                   |
| The placards                       | `chore(picks): 📌 pick this week's placards`                                                                                                                |
| The kit's drawing                  | `chore(markdown): ...`, saying what moved                                                                                                                   |

---

## 🔁 One At A Time

| Workflow             | Concurrency                               | Why                                                                                           |
| :------------------- | :---------------------------------------- | :-------------------------------------------------------------------------------------------- |
| `clock.yml`          | One at a time, none cancelled             | A run by hand waits for a scheduled tick, and then finds nothing left to do                   |
| `markdown.yml`       | One at a time, none cancelled             | Two drawings at once could leave the page a move behind; the one that waits draws it as it is |
| `picks.yml`          | One at a time on a branch, none cancelled | -                                                                                             |
| `games-tests.yml`    | A newer push cancels the older run        | The older result is moot                                                                      |
| The games' workflows | None, on purpose                          | A group cancels waiting runs, which would lose their replies                                  |
| `notes.yml`          | None                                      | -                                                                                             |

In a group that cancels nothing, GitHub keeps only the newest waiting run.
A push that loses the race is tried again: the games and the clock make five
attempts in all, each from the state that won, and Notes and Picks three,
rebasing onto it.

---

## 🔗 See also

- [`.github/workflows/`](../../.github/workflows/README.md) - the workflows
  themselves, each with its triggers
- [How The Games Run](../technical/How-The-Games-Run.md) - what a game's run
  and the clock do, step by step
- [How The Page Is Drawn](../technical/How-The-Page-Is-Drawn.md) - what the
  Markdown, Notes and Picks runs draw

---

<div align="center">

**A run for every move, and a slot for every week.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
