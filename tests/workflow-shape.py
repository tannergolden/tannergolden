# SPDX-FileCopyrightText: 2026 Tanner Golden
# SPDX-License-Identifier: MIT
"""The two workflows keep the properties the design depends on."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = yaml.safe_load((ROOT / ".github/workflows/journal.yml").read_text(encoding="utf-8"))
CHECKS = yaml.safe_load((ROOT / ".github/workflows/checks.yml").read_text(encoding="utf-8"))
JOB = JOURNAL["jobs"]["write"]


def test_the_cron_is_hourly_and_off_the_hour():
    (cron,) = [s["cron"] for s in JOURNAL[True]["schedule"]]
    minute, hour, *_ = cron.split()
    assert minute.isdigit() and minute != "0" and hour == "*"


def test_a_rehearsal_is_gated_on_the_event_not_on_a_field_schedule_events_lack():
    expression = JOB["env"]["JOURNAL_NO_PUSH"]
    assert "github.event_name == 'workflow_dispatch' &&" in expression
    assert "github.ref_name != github.event.repository.default_branch" in expression


def test_writers_share_one_group_and_the_probe_has_its_own():
    assert JOURNAL["concurrency"]["cancel-in-progress"] is False
    assert "inputs.mode == 'probe' && 'probe' || 'write'" in JOURNAL["concurrency"]["group"]
    assert set(JOURNAL[True]["workflow_dispatch"]["inputs"]["mode"]["options"]) == {"tick", "entry", "refresh", "probe"}


def test_the_token_is_least_privilege_and_the_committer_is_the_bot():
    assert JOURNAL["permissions"] == {} and JOB["permissions"] == {"contents": "write"}
    assert CHECKS["permissions"] == {} and CHECKS["jobs"]["test"]["permissions"] == {"contents": "read"}
    assert JOB["env"]["GIT_COMMITTER_NAME"] == "github-actions[bot]"


def test_every_third_party_action_is_pinned_to_a_commit():
    for workflow in (JOURNAL, CHECKS):
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                uses = step.get("uses", "")
                if not uses or uses.startswith("tannergolden/"):
                    continue  # first party is pinned to a tag by house convention
                assert re.match(r"^[\w.-]+/[\w.-]+@[0-9a-f]{40}$", uses), uses


def test_nothing_fetched_can_reach_a_run_block():
    text = (ROOT / ".github/workflows/journal.yml").read_text(encoding="utf-8")
    for block in re.findall(r"^\s+run: (.*)$", text, flags=re.MULTILINE):
        assert "${{" not in block, block
