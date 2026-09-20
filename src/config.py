# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""Every tunable this repository has, in one place.

THE ONE NUMBER THAT MATTERS is MEAN_INTERVAL_HOURS. Everything about the
cadence follows from it: the entry count per day, how often the page looks
stale, and how long a run spends asleep. It is a mean, not a period. Waits
are drawn from an exponential distribution, so the gap between two entries
is sometimes minutes and sometimes days, and neither is a bug.

An environment variable overrides any of these, which is how the workflow
runs a dry rehearsal without editing the file it is rehearsing.
"""

from __future__ import annotations

import os

# --- Cadence ---------------------------------------------------------------

# The mean wait between dispatches. At 12 hours the process averages two a
# day, leaves roughly one day in seven with nothing at all, and goes
# quiet for more than 48 hours about six times a year. That silence is the
# point: a page that posts every day on schedule is a page nobody believes is
# random.
MEAN_INTERVAL_HOURS = float(os.environ.get("DISPATCH_MEAN_HOURS", "12"))

# How far ahead one run is willing to wait. The cron fires hourly, so a run
# handles anything due inside the coming hour and leaves the rest to its
# successor. Slightly under an hour so a late cron cannot have two runs
# reaching for the same entry.
HORIZON_SECONDS = int(os.environ.get("DISPATCH_HORIZON_SECONDS", str(58 * 60)))

# The mean wait between full page refreshes (date line, the three daily
# modules, the cards). Drawn the same way as an entry, so the refresh lands
# at an unremarkable hour rather than on a tidy cron boundary.
MEAN_REFRESH_HOURS = float(os.environ.get("DISPATCH_REFRESH_HOURS", "24"))

# Dispatches sent on the very first run, before any state exists, so the page
# is populated rather than empty while it waits for the first random moment.
BOOTSTRAP_ENTRIES = int(os.environ.get("DISPATCH_BOOTSTRAP", "3"))

# --- Presentation ----------------------------------------------------------

DISPLAY_TIMEZONE = os.environ.get("DISPATCH_TIMEZONE", "America/New_York")

# The commit subject ceiling. Conventional Commits allows 100; the house
# standard says keep it under 72 and this holds to that.
MAX_SUBJECT_LENGTH = 72

# Body prose wraps here, per the commit standard.
BODY_WRAP = 72

# Dispatches shown open on the page, and the size of the collapsed block beneath.
ENTRIES_VISIBLE = 3
ENTRIES_COLLAPSED = 10

# A borrowed snippet stops here. Three things at once: it keeps a quotation a
# quotation rather than a reproduction, it stays under the 20-line threshold
# where the styling standard demands a collapsible block, and it keeps a
# commit body readable in `git log`.
MAX_SNIPPET_LINES = 15
MAX_SNIPPET_CHARS = 800

# --- Provenance ------------------------------------------------------------

# Flip to False and `refactor(rosetta)` cites the task without reproducing
# the code. The kind survives, the GFDL exposure does not. Nothing else in
# this repository reproduces a copyleft work, so this is the whole switch.
REPRODUCE_ROSETTA_CODE = os.environ.get("DISPATCH_ROSETTA_CODE", "1") != "0"

# --- Identity --------------------------------------------------------------

# Read rather than invented. The contribution graph resolves the AUTHOR of a
# commit, so this address is what makes a generated entry count as the work of
# the person who built and scheduled the generator. The committer is the
# Actions identity, set in the workflow: the object then records both that
# Tanner owns this and that a machine performed it.
AUTHOR_NAME = os.environ.get("DISPATCH_AUTHOR_NAME", "Tanner Golden")
AUTHOR_EMAIL = os.environ.get(
    "DISPATCH_AUTHOR_EMAIL", "24684994+tannergolden@users.noreply.github.com"
)

# Sent on every outbound request. The Wikimedia APIs reject a request without
# one, and every other source here is a volunteer project entitled to know who
# is calling and where to complain.
USER_AGENT = (
    "tannergolden-dispatches/1.0 (+https://github.com/tannergolden/tannergolden; "
    "one request per source, at most a few times a day)"
)

# --- Paths -----------------------------------------------------------------

README = "README.md"
DISPATCH_DIR = "dispatches"
STATE_DIR = "state"
ASSETS_DIR = "assets"
SCHEDULE_FILE = "state/schedule.json"
LEDGER_FILE = "state/ledger.json"
