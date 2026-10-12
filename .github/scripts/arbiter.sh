# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
# shellcheck shell=bash
#
# The Arbiter's words on the owner's play repository, sourced by chess.yml:
#
#   say ISSUE FILE         comment on a move's issue, then lock it, so nobody but the owner and the Arbiter can write
#                          there again: a player can never use their issue to notify the owner whenever they like
#   desk LABEL TITLE BODY  the number of the Arbiter's own open issue with that label, opened and locked if there is
#                          none: `arbiter-logbook` for the moves it plays for a side that let a week pass, and
#                          `arbiter-outage` for a failure, so the owner is told once however many moves it stops
#   settle                 close the outage notice, if one is open, now that a move has gone through
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
