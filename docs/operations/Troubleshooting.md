<!--
title: '🩺 TROUBLESHOOTING'
description: 'What to do when a move is not ruled on or gets no reply, a board is not redrawn, the Arbiter moves late, or a run fails on a game''s state or the settings: each symptom, what the run log says, and the way back. Read it when anything on the profile looks stuck.'
type: guide
keywords: [runbook, outage, arbiter, errors, recovery, logs, stuck]
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🩺 TROUBLESHOOTING

<a name="top"></a>

**Each way the profile can get stuck, what the run says, and the way back.**

_Read the run before you touch the state._

</div>

---

## 🧭 Where To Look

- **The run**, on this repository's Actions tab. Each engine prints one line a
  run, such as `Move g8f6 (game 1, move 2, @player-1): played 1... Nf6.`, and
  the clock one line a game, such as
  `chess: the side to move has until 2026-10-24T10:55:58Z.`. A failure is an
  `::error::` line, or a traceback, in the step that failed.
- **The move's issue** on tannergolden/play: the Arbiter's reply, its ruling's
  label and its milestone.
- **The Arbiter's two notices** on tannergolden/play: the open issue labelled
  `arbiter-outage` while moves are failing, and its logbook, labelled
  `arbiter-logbook`.

---

## 🧯 A Move Was Not Ruled On

**What you see.** The move's issue says _The Arbiter couldn't rule on ..., so
nothing was played_, and stays open. The outage notice, _🧯 The Arbiter is
down_, is open on tannergolden/play, and mentioned the owner once.

**What happened.** A game's run read the move back from its issue, then failed
before the game ruled on it, in the engine or in the save. Every move it stops
links to the same notice, and nobody is mentioned again.

- [ ] Open the run the notice links, and read the failed step's error in
      [Errors At A Glance](#-errors-at-a-glance).
- [ ] Fix the cause on Development.
- [ ] Nothing more is needed for the moves. The next move that goes through
      closes the notice, and tannergolden/play sends the moves left waiting
      again, as its
      [How A Move Travels](https://github.com/tannergolden/play#-how-a-move-travels)
      says. A move sent again is played on the latest state, or turned away
      if the board has moved on, and one already played from its issue is
      never played twice.

---

## 🔇 A Move Was Played, But Got No Reply

**What you see.** The move is on the board, but its issue has no reply and
stays open; the run failed at _🔑 Mint the reply token_ or _💬 Reply on the
move_. The clock's runs may fail the same way at _🔑 Mint the notice token_.

**What happened.** The game saved the move and the page was redrawn, but the
Arbiter could not speak: the Official Arbiter App's `PLAY_APP_CLIENT_ID`
variable or `PLAY_APP_PRIVATE_KEY` secret is missing or wrong. No outage
notice is opened, since that is only for a run that fails before the game
rules.

- [ ] Put the App's two credentials right:
      [Workflows & Schedules](../references/Workflows-&-Schedules.md)
      says where each is read, and play's
      [GitHub App](https://github.com/tannergolden/play/blob/Development/docs/operations/GitHub-App.md)
      guide how to set them up and rotate the key.
- [ ] A run of the same move over again, from its issue, then finds it
      already played, answers it and rules it `played`.

---

## ⚠️ A Run Passed With Warnings

The reply is already on the issue, so what failed is only what comes after
it. Each of these is a warning in the run's log, never a failed move, and the
game goes on unaffected.

| Warning                                                          | Means                                                     |
| :--------------------------------------------------------------- | :-------------------------------------------------------- |
| `#N was left unlocked.`                                          | The issue could not be locked after the reply             |
| `#N was left without its <ruling> label.`                        | The `played` or `turned away` label could not be added    |
| `#N was left out of <Game> · game <N>, which could not be made.` | The game's milestone did not exist, and could not be made |
| `#N was left out of <Game> · game <N>.`                          | The issue could not be filed in its milestone             |
| `#N was left open: it could not be closed as <ruling>.`          | The issue could not be closed                             |

---

## 🖼️ A Board Was Not Redrawn

**What you see.** A move was played and its issue answered, but the page still
shows the board before it.

**What happened.** The move's run wrote the new board into the settings and
started 📝 Markdown, which draws the page in a run of its own. Those runs never
overlap: one that starts while another draws waits for it, and GitHub keeps
only the newest waiting run, which draws the page as it is by then. A game's
run starts a drawing only when `changed` is true: the game moved on, its board
was set out anew, or its last move was sent again.

- [ ] Look at the latest 📝 Markdown runs: one still waiting or drawing draws
      this board too.
- [ ] If one failed, any later run draws the whole page again: the next move
      or tick that changes a board, a pick that moves a placard, or the daily
      run at midnight EST. The kit's README says how to
      [check a page](https://github.com/tannergolden/markdown#-checking-a-page).

---

## ⏰ The Arbiter Moved Late

- **The clock runs at 17 and 47 minutes past every hour**, so the Arbiter's
  move lands within about half an hour of its deadline, or later when GitHub
  runs the clock late or drops a tick. Every check counts from the state, so
  the next tick catches up.
- **Each Clock run logs one line a game**, such as
  `the side to move has until <time>` (the week is not up),
  `game <N>'s final board is up until <time>`, or `no game has started`
  (Chess, before the owner's first move).
- **A failing Clock run stops all four games.** One run saves every game, so
  one game whose state cannot be read stops the tick for all of them: see
  the next section.

---

## 📦 A Game's State Will Not Load

**What you see.** Every run of one game fails, and so does every Clock run,
with `game <N>, move <M>: <move> is not legal there`; or every game's run
fails on a file under `.github/<game>/` that is not valid JSON.

**What happened.** A file the game's runs keep was changed by something else.
Every run replays its game from the first move, so a move that is not legal
where it stands stops that game and the clock; and every game's run reads all
four games' state for the Hall of Fame, so a file that is not JSON stops them
all.

- [ ] Find the commit that changed it: the runs' own commits are
      `github-actions[bot]`'s, `chore(<game>): ...` or `chore(games): ...`.

```bash
git log --format='%h %an %s' -- .github/chess/
```

- [ ] Revert that commit, so the file is again as the last run wrote it.
- [ ] Moves stopped meanwhile come back as in
      [A Move Was Not Ruled On](#-a-move-was-not-ruled-on).

---

## 🔧 The Settings Will Not Take A Board

**What you see.** A run fails with
`the settings need one '# <name>:start' line, then one '# <name>:end' line, under elements:`,
or `the settings have no elements: section to set the boards out in`; or
Picks fails with `expected one '# <name>:start' line, and one '# <name>:end' line after it`.

**What happened.** An edit to `.github/markdown.yaml` doubled, dropped or
swapped a region's marker lines, or took `elements:` away. Every run that
writes the broken region fails: its own game's and the clock's, every game's
for `hall`, and its picker's for `releases` or `issues`.

- [ ] Give each region one start line and one end line under `elements:`,
      the start first. A game's region or the hall's with both lines gone is
      added back by the next run that writes it; a placard region is not, so
      put its two lines back by hand.
- [ ] Leave the lines between the markers alone: the next run writes them
      again.

---

## 📝 The Notes Or The Placards Did Not Change

- **`nothing moved`** in a Notes or Picks run means the block or the placards
  came out the same, and nothing was committed.
- **Notes runs `test_notes.py` before it draws**, so a library that breaks it
  stops the Field Notes: a kind not at 1,000 notes or a level not at 250, two
  notes of a kind that say the same thing, a missing field, an unknown level,
  or an en dash, em dash or horizontal bar.
  [How The Page Is Drawn](../technical/How-The-Page-Is-Drawn.md#changing-the-library)
  has the library's rules.
- **An open source that is down** logs
  `<kind>: open data unavailable (...); a curated note stands in`, and that
  week's alert comes from the library.
- **A picker that cannot reach GitHub** logs a notice and keeps last week's
  placards.
- **A push that keeps losing the race** fails with
  `could not push to <branch> after three attempts`; a run by hand, or next
  week's, draws again.

---

## 🔍 Errors At A Glance

| Error                                                                             | From                  | Means                                                                                                     |
| :-------------------------------------------------------------------------------- | :-------------------- | :-------------------------------------------------------------------------------------------------------- |
| `Issue #N does not hold this move from this player, so nothing was played.`       | a game's read-back    | The issue's title or author is not the move the run was started with. Nothing is said on the issue        |
| `A move with no issue is the owner's alone to run, so nothing was played.`        | a game's read-back    | Someone other than the owner started a game's workflow without an issue                                   |
| `No move was sent: this workflow only plays moves, and clock.yml keeps the time.` | a game's read-back    | A game's workflow was started without a move                                                              |
| `There is no game called '<key>' here, so nothing was played.`                    | `game.yml`            | It was called with a key other than `tictac`, `pentago` or `checkers`                                     |
| `The move was not played: <INPUT> is missing or malformed.`                       | an engine             | An input is not in the form the intake sends, and there is no issue to answer it on                       |
| `could not save the game to <branch> after five attempts`                         | a game's save         | Five pushes in a row lost the race or were refused; the move's issue is answered as in the first section  |
| `could not save the games to <branch> after five attempts`                        | the clock's save      | The same, for the clock: no game moved on in that tick                                                    |
| `game <N>, move <M>: <move> is not legal there`                                   | an engine             | A game's state does not replay: [A Game's State Will Not Load](#-a-games-state-will-not-load)             |
| `the settings need one '# <name>:start' line, ...`                                | an engine             | A region's markers are broken: [The Settings Will Not Take A Board](#-the-settings-will-not-take-a-board) |
| `OWNER and OWNER_ID name the house, and one is missing or malformed.`             | an engine run by hand | The owner's login and account ID were not given; in Chess the message names the player of White           |

---

## 🧪 Reproducing A Run Offline

Every engine takes its state folder, the settings, an output folder and the
time as arguments, and the move as the environment its workflow sets, so a
failed run can be played again on a copy, with no network and nothing in the
checkout touched. Copy all four games, since every run reads each one's state
for the Hall of Fame, and take the inputs and the time from the run's log:

```bash
work="$(mktemp -d)"
cp -r .github/chess .github/checkers .github/pentago .github/tictac .github/markdown.yaml "$work"
env -u GH_TOKEN -u GITHUB_TOKEN -u MARKDOWN_TOKEN \
  OWNER=tannergolden OWNER_ID=24684994 \
  UCI=g8f6 GAME=1 MOVE_NUMBER=2 ISSUE=1 PLAYER=player-1 PLAYER_ID=1001 \
  python3 .github/scripts/chess.py "$work/chess" \
  --settings "$work/markdown.yaml" --out "$work/out" --now 2026-10-20T12:00:00Z
cat "$work/out/comment.md" "$work/out/commit.txt"
```

- **Tic-Tac, Pentago or Checkers**: `python3 .github/scripts/games.py <game> "$work/<game>"`,
  with the same flags, and `MOVE` in place of `UCI`.
- **The clock**: `python3 .github/scripts/clock.py "$work"`, with the same
  flags, and `OWNER` and `OWNER_ID` alone; `notices.txt` in the output folder
  lists the issue, or the logbook, that each notice would go on.

---

## 🔗 See also

- [How The Games Run](../technical/How-The-Games-Run.md) - every step a move's
  run takes, and the Arbiter's notices
- [Game State](../references/Game-State.md) - every field of the files a game
  keeps
- [When A Move Fails](https://github.com/tannergolden/play/blob/Development/docs/operations/GitHub-App.md#-when-a-move-fails) -
  tannergolden/play's side of the same failures
- [Troubleshooting](https://github.com/tannergolden/standards/blob/Development/docs/operations/Troubleshooting.md) -
  the standards' own, for what every repository shares

---

<div align="center">

**Read the run, mend the cause, and the moves come back by themselves.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
