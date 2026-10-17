# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
# shellcheck shell=bash
#
# The Arbiter's words on the owner's play repository, sourced by chess.yml, game.yml and clock.yml:
#
#   say ISSUE FILE         comment on a move's issue, then lock it, so nobody but the owner and the Arbiter can write
#                          there again: a player can never use their issue to notify the owner whenever they like
#   desk LABEL TITLE BODY  the number of the Arbiter's own open issue with that label, opened and locked if there is
#                          none: `arbiter-logbook` for the moves it plays for a side that let a week pass, and
#                          `arbiter-outage` for a failure, so the owner is told once however many moves it stops
#   settle                 close the outage notice, if one is open, now that a move has gone through
#   rule ISSUE RULING NAME GAME
#                          after the reply on a player's move, close its issue with the ruling: `played` closes it
#                          as completed and `turned away` as not planned, under a label of the same name, in the
#                          milestone `NAME · game GAME` when GAME is given; `stranded` and `overdue`, the
#                          intake's marks on a move still waiting, come off, and so does the other ruling. Labels and
#                          milestones are made the first time they are needed. Any part that fails is a warning,
#                          never a failed move: the reply is already there
#   milestone_of TITLE     the number of the play repository's milestone of that title, open or closed, for rule
#
# Needs GH_TOKEN, with Issues write on the play repository, PLAY (owner/play) and RUN_URL.

say() {
  local issue=$1 file=$2
  # The Arbiter may come back to a locked issue, to say what it played after a week: it unlocks the issue to speak
  # when it must, and locks it again.
  if ! gh issue comment "$issue" --repo "$PLAY" --body-file "$file" > /dev/null 2>&1; then
    gh issue unlock "$issue" --repo "$PLAY" > /dev/null 2>&1 || true
    gh issue comment "$issue" --repo "$PLAY" --body-file "$file" > /dev/null
  fi
  if [ "$(gh api "repos/$PLAY/issues/$issue" --jq .locked)" != true ]; then
    gh issue lock "$issue" --repo "$PLAY" --reason resolved > /dev/null 2>&1 || echo "::warning::#$issue was left unlocked."
  fi
}

desk() {
  local label=$1 title=$2 body=$3 number
  number="$(gh issue list --repo "$PLAY" --label "$label" --state open --limit 1 --json number --jq '.[0].number // empty')"
  if [ -z "$number" ]; then
    gh label create "$label" --repo "$PLAY" --color 6e7781 --description "The Arbiter's own notices" --force > /dev/null
    number="$(gh issue create --repo "$PLAY" --title "$title" --body "$body" --label "$label")"
    number="${number##*/}"
    gh issue lock "$number" --repo "$PLAY" --reason resolved > /dev/null 2>&1 || echo "::warning::#$number was left unlocked."
  fi
  echo "$number"
}

settle() {
  local number
  for number in $(gh issue list --repo "$PLAY" --label arbiter-outage --state open --json number --jq '.[].number'); do
    printf '%s\n' "✅ **The Arbiter is back**: [a move just went through]($RUN_URL), so this is closed." \
      > "$RUNNER_TEMP/settled.md"
    say "$number" "$RUNNER_TEMP/settled.md"
    gh issue close "$number" --repo "$PLAY" --reason completed > /dev/null
  done
}

rule() {
  local issue=$1 ruling=$2 name=$3 game=$4 reason other colour description title milestone stale
  case "$ruling" in
    played)
      reason=completed other='turned away' colour=0e8a16
      description="✅ The Arbiter played this move: it's on the board."
      ;;
    'turned away')
      reason=not_planned other=played colour=b60205
      description="⛔ The Arbiter turned this move away: it wasn't played."
      ;;
    *) return 0 ;; # the clock's own run, or nothing to rule on
  esac
  [[ "$issue" =~ ^[1-9][0-9]{0,15}$ ]] || return 0
  # Made the first time it is needed, and never recoloured after.
  if ! gh api "repos/$PLAY/labels/${ruling// /%20}" --silent > /dev/null 2>&1; then
    gh label create "$ruling" --repo "$PLAY" --color "$colour" --description "$description" > /dev/null 2>&1 || true
  fi
  gh api --method POST "repos/$PLAY/issues/$issue/labels" -f "labels[]=$ruling" --silent > /dev/null 2>&1 \
    || echo "::warning::#$issue was left without its $ruling label."
  # The other ruling comes off too, should a run made over again rule otherwise.
  for stale in stranded overdue "$other"; do
    gh api --method DELETE "repos/$PLAY/issues/$issue/labels/${stale// /%20}" --silent > /dev/null 2>&1 || true
  done
  case "$name" in Chess | Checkers | Pentago | Tic-Tac) ;; *) name='' ;; esac
  if [ -n "$name" ] && [[ "$game" =~ ^[1-9][0-9]{0,8}$ ]]; then
    title="$name · game $game"
    milestone="$(milestone_of "$title")"
    if [ -z "$milestone" ]; then
      # Made by the game's first move to be ruled on, or by one ruled on at the same moment as this, so it is
      # looked for again either way.
      gh api --method POST "repos/$PLAY/milestones" -f "title=$title" \
        -f "description=Every move sent for $name game $game on @${PLAY%%/*}'s profile." --silent > /dev/null 2>&1 \
        || true
      milestone="$(milestone_of "$title")"
    fi
    if [ -z "$milestone" ]; then
      echo "::warning::#$issue was left out of $title, which could not be made."
    elif ! gh api --method PATCH "repos/$PLAY/issues/$issue" -F "milestone=$milestone" --silent > /dev/null 2>&1; then
      echo "::warning::#$issue was left out of $title."
    fi
  fi
  # The REST call, not `gh issue close`, so a move closed before the game ruled on it still takes its reason.
  gh api --method PATCH "repos/$PLAY/issues/$issue" -f state=closed -f "state_reason=$reason" --silent \
    > /dev/null 2>&1 || echo "::warning::#$issue was left open: it could not be closed as $ruling."
  return 0
}

# The number of the play repository's milestone titled TITLE, open or closed, or nothing when there is none.
milestone_of() {
  local title=$1 number shown
  while IFS=$'\t' read -r number shown; do
    if [ "$shown" = "$title" ] && [[ "$number" =~ ^[1-9][0-9]*$ ]]; then
      echo "$number"
      return 0
    fi
  done < <(gh api --paginate "repos/$PLAY/milestones?state=all&per_page=100" \
    --jq '.[] | [.number, .title] | @tsv' 2> /dev/null)
  return 0
}
