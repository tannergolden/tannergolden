<!--
title: '🖌️ HOW THE PAGE IS DRAWN'
description: 'How README.md is put together: the blocks the Markdown Kit draws and the settings it reads, the regions the games and the pickers write, the weekly placards, and the Field Notes with their library. Read it before editing README.md, .github/markdown.yaml or a file of notes.'
type: guide
-->

<!-- markdownlint-disable MD041 -->
<div align="center">

# 🖌️ HOW THE PAGE IS DRAWN

<a name="top"></a>

**Every block on the profile, the run that draws it, and the settings it reads.**

_Typed around the markers, drawn between them._

</div>

---

## 💡 The Page, Block By Block

| Block                | In `README.md`                                                                       | Drawn by   | From                                                   |
| :------------------- | :----------------------------------------------------------------------------------- | :--------- | :----------------------------------------------------- |
| Header and badges    | `markdown:header`, `markdown:badges`                                                 | the kit    | GitHub's figures, and `banners:` and `badges:`         |
| About Me             | none                                                                                 | by hand    |                                                        |
| Play Against Me      | its prose by hand, then `markdown:element:chess`, `checkers`, `pentago` and `tictac` | the kit    | each game's region of the settings                     |
| Hall of Fame         | `markdown:element:hall-of-fame`                                                      | the kit    | the `hall` region                                      |
| How It Fits Together | its prose by hand, then `markdown:element:how-it-fits`                               | the kit    | the `how-it-fits` element, written by hand             |
| Trophies             | `markdown:trophies`                                                                  | the kit    | GitHub's figures, and `trophies:`                      |
| Latest Releases      | `markdown:element:release-1`, `release-2`                                            | the kit    | the `releases` region                                  |
| Field Notes          | `notes:start`, `notes:end`                                                           | `notes.py` | the library in `.github/notes/`, and five open sources |
| Good First Issue     | `markdown:element:issue-1`, `issue-2`                                                | the kit    | the `issues` region                                    |
| Footer               | `markdown:footer`                                                                    | the kit    | `banners:`                                             |

Each of the kit's blocks lies between `<!-- markdown:<part>:start -->` and its
`:end` twin, and the Field Notes between `<!-- notes:start -->` and
`<!-- notes:end -->`. Everything between a pair is written by its run, so a
hand edit there is gone on the next one; everything outside them is typed. A
game's block is its board, the list of moves that can be played under it, and
its note.

---

## 🚀 The Kit's Run

[`markdown.yml`](../../.github/workflows/markdown.yml) is the stub the kit's
README gives every page, with this page's choices: `mode: profile`,
`theme: medieval-illuminated` (the medieval collection's Illuminated, all
year), `sign: capricorn` (the roundel every header carries) and
`holidays: 'true'` (a holiday's set takes the page around its day, then hands
it back). It calls the kit's workflow at `@v1` and hands it `MARKDOWN_TOKEN`
and no other secret.

- **When it runs**: every day at 05:00 UTC, which is midnight EST, so the
  page's day, and a holiday's set with it, changes at the page's own midnight;
  and whenever Picks has new placards, a move changes a board, or a tick of
  the clock changes one.
- **What it writes**: the README's blocks, everything under `assets/` and the
  lock, `.github/markdown.lock.json`, in one commit.
- **One drawing at a time.** Two runs at once could each push the boards as
  they stood when they began, so the older could land last and leave the page
  a move behind. A run that starts while one is drawing waits for it, then
  draws the page as it is by then, and GitHub keeps only the newest waiting
  run.
- **The birthday**: on the day `birthday:` names in the settings, the whole
  page is drawn in the kit's Birthday set.

The kit's README says what a run does inside, in
[One Stub](https://github.com/tannergolden/markdown#-one-stub) and
[How A Run Draws A Page](https://github.com/tannergolden/markdown#-how-a-run-draws-a-page),
and how its check mode catches a hand edit, in
[Checking A Page](https://github.com/tannergolden/markdown#-checking-a-page).

---

## ⚙️ The Settings

[`.github/markdown.yaml`](../../.github/markdown.yaml) is what the kit reads
on every run. Whatever it does not say is read from GitHub: the name, the bio
and every figure. Every key and its default are in the kit's
[Settings](https://github.com/tannergolden/markdown/blob/Development/docs/references/Settings.md)
reference.

| Part                                                    | Written by                      | Holds                                                                       |
| :------------------------------------------------------ | :------------------------------ | :-------------------------------------------------------------------------- |
| `timezone`, `birthday`                                  | hand                            | EST for every time on the page, and the day of the Birthday set             |
| `banners:`                                              | hand                            | The motto, the notes, the figures, the closing and the footer's links       |
| `badges:`                                               | hand                            | Three static badges, and two the run measures: Standards CI and Last Commit |
| `elements:`, `how-it-fits`                              | hand                            | The schematic: its boxes, its wires and their notes                         |
| `# releases:start` to `# releases:end`                  | `releases.py`, through Picks    | The two latest releases' placards                                           |
| `# issues:start` to `# issues:end`                      | `issue.py`, through Picks       | The two good first issues' placards                                         |
| The `tictac`, `pentago`, `checkers` and `chess` regions | each game's runs, and the clock | Each game's board, its moves and its note                                   |
| `# hall:start` to `# hall:end`                          | the games' runs, and the clock  | The Hall of Fame of all four games                                          |
| `trophies:`                                             | hand                            | The trophies' style, and the five core trophies                             |

The regions lie under `elements:`, and each writer rewrites the lines of its
own regions alone, and only when they changed:

- **Keep one start line and one end line for each region, the start first.**
  A game's region or the hall's that breaks fails every run that writes it;
  a placard region that breaks stops its picker.
- **A game's region or the hall's whose two lines are both gone** is added
  back at the end of `elements:` by the next run that writes it. A placard
  region is not: its picker stops until both lines are back.
- **Leave the lines between the markers alone.** What the games write there is
  in [Game State](../references/Game-State.md#-the-regions-the-games-write).

---

## 📌 The Placards

[`picks.yml`](../../.github/workflows/picks.yml) runs at 09:30 EST (14:30 UTC):
on Wednesdays for the latest releases, on Fridays for the good first issues,
and for both when it is run by hand. Each picker's tests run first. When a
placard moved, it commits `.github/markdown.yaml`, as
`chore(picks): 📌 pick this week's placards`, and starts 📝 Markdown, so the
new placards are drawn straight away rather than at midnight.

|                       | Latest Releases, `releases.py`                                                                                                                                                                                              | Good First Issue, `issue.py`                                                                                                                                                                                                            |
| :-------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Looks at              | The account's public repositories, without forks or archived ones, and each one's latest release, never a draft or a prerelease                                                                                             | The 60 most-starred public projects, each with at least 1,000 stars, that have open `good first issue` issues                                                                                                                           |
| Picks                 | The two whose latest release came out most recently                                                                                                                                                                         | From the most-starred projects first, each project's newest issue opened in the past week, or the past month in a quiet week, that is still open, unassigned, unlocked and has no pull request on the way: two projects, one issue each |
| Shows                 | The repository's description, the version, the day it came out, and `@V1` where the moving major tag stands beside it, else the language; it links to the repository's latest release, since superseded releases are pruned | The stars, the language and the day it opened, with the issue's number and title; it links to the issue                                                                                                                                 |
| When nothing is found | Last week's placards stay; a first run writes nothing                                                                                                                                                                       | Last week's placards stay; a first run writes a placard that opens GitHub's own search                                                                                                                                                  |

Every title and description from GitHub is cut down to plain text the kit can
letter.

---

## 📝 The Field Notes

[`notes.yml`](../../.github/workflows/notes.yml) redraws the block between
`<!-- notes:start -->` and `<!-- notes:end -->` on Mondays at 09:30 EST (14:30
UTC). It clones tldr-pages' `pages/common` (without them, the Tip falls back
to the library), runs `test_notes.py`, draws the week with `notes.py`, and
commits the README only when the block moved, as
`chore(notes): 📝 redraw the field notes`.

**A week is five alerts**, one of each kind in GitHub's order: Note, Tip,
Important, Warning, Caution. For each, a coin seeded by the week chooses an
open source instead of the library about half the time, and a source that
cannot be read, or has nothing recent, hands its alert back to the library, so
the block is always whole. Every choice is seeded by the week, so a run made
again in the same week makes the same choices.

| Alert     | Open source                          | Looks at                                                                                                                                       |
| :-------- | :----------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------- |
| Note      | GitHub's changelog                   | Changes shipped in the last seven days                                                                                                         |
| Tip       | tldr-pages                           | One command example from `pages/common`                                                                                                        |
| Important | endoflife.date                       | A release of one of 18 runtimes, databases and platforms losing its security fixes in the next six months, or that lost them in the last three |
| Warning   | GitHub Advisory Database             | Reviewed critical and high advisories published in the last seven days, in one of 11 ecosystems                                                |
| Caution   | CISA Known Exploited Vulnerabilities | Vulnerabilities added to the catalogue in the last fourteen days                                                                               |

**The library** is one TOML file for each kind in
[`.github/notes/`](../../.github/notes/README.md), each note a `[[note]]`
table:

```toml
[[note]]
level = "beginner"
topic = "Git"
text = "Stage part of a file with `git add -p`: Git shows each change in turn, so a commit holds one idea instead of everything you touched."
```

The kind in place `k` of GitHub's order shows the level in place
`(week + k) mod 4` of beginner, intermediate, advanced and professional, so
every week has all four levels, and each level's 250 notes are walked in a
fixed shuffled order, one every four weeks: about nineteen years before a
note comes round again.

### Changing The Library

- [ ] **Keep each kind at 1,000 notes, 250 at each level.** `test_notes.py`
      holds the library to those counts, and the Monday run runs it before it
      draws, so a library that grows without its test changing in the same
      commit stops the Field Notes.
- [ ] **Replace a note in place to keep its weeks.** A level's order is
      shuffled by position, so a replacement shows in the weeks the old note
      did, while adding or removing a note reshuffles its level's whole order.
- [ ] **Give every note a `level`, a `topic` and a `text` of one line**, the
      level one of the four, say nothing another note of its kind says, and
      use no en dash, em dash or horizontal bar. The run stops on any of
      these, naming the file and the note's number where it can.
- [ ] **Check it offline before the push.** `--offline` reads the library
      alone and `--today` draws any week; pointed at a copy, `notes.py`
      leaves the README as it is.

```bash
env -u GH_TOKEN -u GITHUB_TOKEN -u MARKDOWN_TOKEN \
  python3 -m unittest discover -s .github/scripts -p 'test_notes.py'
preview="$(mktemp)"
cp README.md "$preview"
python3 .github/scripts/notes.py "$preview" --offline --today 2026-10-26
sed -n '/notes:start/,/notes:end/p' "$preview"
```

---

## 🔗 See also

- [Overview](../introduction/Overview.md) - what lives where, and which run
  writes each file
- [Workflows & Schedules](../references/Workflows-&-Schedules.md) - every
  run's time, permissions, secrets and commits
- [Markdown Kit](https://github.com/tannergolden/markdown) - the kit that
  draws the page, and its README's live example

---

<div align="center">

**Settings in, drawings out, and the prose around them yours.**

[↑ Back to Top](#top)

<br />

Built with ❤️ by the Engineering Team. Distributed under the MIT License.

</div>
