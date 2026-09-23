# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The two workflows keep the properties the design depends on."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DISPATCHES = yaml.safe_load((ROOT / ".github/workflows/dispatches.yml").read_text(encoding="utf-8"))
CHECKS = yaml.safe_load((ROOT / ".github/workflows/checks.yml").read_text(encoding="utf-8"))
JOB = DISPATCHES["jobs"]["write"]


def test_the_cron_is_hourly_and_nothing_is_due_at_it():
    """Hourly, on the hour. The minute the cron fires is not the minute a
    dispatch lands: the run reads the schedule and sleeps until the exact
    second a moment falls due, so a scheduler running late moves when the
    run starts and not when the entry arrives."""
    (cron,) = [s["cron"] for s in DISPATCHES[True]["schedule"]]
    minute, hour, *rest = cron.split()
    assert (minute, hour, rest) == ("0", "*", ["*", "*", "*"]), cron


def test_a_rehearsal_is_gated_on_the_event_not_on_a_field_schedule_events_lack():
    expression = JOB["env"]["DISPATCH_NO_PUSH"]
    assert "github.event_name == 'workflow_dispatch' &&" in expression
    assert "github.ref_name != github.event.repository.default_branch" in expression


def test_writers_share_one_group_and_the_probe_has_its_own():
    assert DISPATCHES["concurrency"]["cancel-in-progress"] is False
    assert "inputs.mode == 'probe' && 'probe' || 'write'" in DISPATCHES["concurrency"]["group"]
    assert set(DISPATCHES[True]["workflow_dispatch"]["inputs"]["mode"]["options"]) == {"tick", "dispatch", "refresh", "probe"}


def test_the_token_is_least_privilege_and_the_committer_is_the_bot():
    assert DISPATCHES["permissions"] == {} and JOB["permissions"] == {"contents": "write"}
    assert CHECKS["permissions"] == {} and CHECKS["jobs"]["test"]["permissions"] == {"contents": "read"}
    assert JOB["env"]["GIT_COMMITTER_NAME"] == "github-actions[bot]"


def test_every_third_party_action_is_pinned_to_a_commit():
    for workflow in (DISPATCHES, CHECKS):
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses", "")
                if not uses or uses.startswith("tannergolden/"):
                    continue  # first party is pinned to a tag by house convention
                assert re.match(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$", uses), uses


def test_nothing_fetched_can_reach_a_run_block():
    text = (ROOT / ".github/workflows/dispatches.yml").read_text(encoding="utf-8")
    for block in re.findall(r"^\s+run: (.*)$", text, flags=re.MULTILINE):
        assert "${{" not in block, block


def test_every_writing_workflow_checks_out_the_badge_kit():
    """render_badges warns and returns when the kit is missing.

    That is the right behaviour for a local run, and silent breakage in CI:
    the page would embed a badge whose image says one thing and whose alt
    text says another. A run that can commit a badge must be able to draw it.
    """
    root = Path(__file__).resolve().parent.parent
    for name in ("dispatches.yml", "availability.yml"):
        text = (root / ".github/workflows" / name).read_text(encoding="utf-8")
        assert "repository: tannergolden/emblems" in text, name
        assert "EMBLEMS_KIT:" in text, name


def test_the_documented_egress_is_what_the_code_actually_fetches():
    """The comment is the allowlist the day the policy moves to block.

    It drifted once already: two feeds were removed for being paywalled and
    their hosts stayed in the list. A stale allowlist is worse than none,
    because it is the one nobody re-derives before pasting it in.
    """
    import sys
    from urllib.parse import urlparse

    sys.path.insert(0, str(ROOT / "src"))
    import feeds
    import support

    fetched = {
        "api.github.com", "raw.githubusercontent.com", "github.com",
        "hacker-news.firebaseio.com", "lobste.rs",
        urlparse(support.API).netloc,
        *(urlparse(feed.url).netloc for feed in feeds.FEEDS),
    }
    text = (ROOT / ".github/workflows/dispatches.yml").read_text(encoding="utf-8")
    block = text.split("for that allowlist:")[1].split("#\n")[0]
    documented = {host for host in re.split(r"[\s,#]+", block) if "." in host}
    assert documented == fetched, f"missing {fetched - documented}, stale {documented - fetched}"
