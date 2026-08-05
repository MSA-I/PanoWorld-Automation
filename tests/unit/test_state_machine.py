"""Structural enforcement of contracts/state_machine.yaml (PLAN-000 T4, AC5).

The file is JSON-syntax (a valid YAML subset) so json stdlib parses it — see
contracts/README.md.
"""
from __future__ import annotations

import json

from tests.conftest import REPO_ROOT

SM = json.loads((REPO_ROOT / "contracts" / "state_machine.yaml").read_text(encoding="utf-8"))

STATES = set(SM["states"])
TERMINAL = set(SM["terminal_states"])
POLICY_STATES = {"REWORK", "BLOCKED", "CANCELLED"}  # governed by policies, not row transitions
TRANSITIONS = SM["transitions"]
GATES = SM["gates"]


def test_all_gate_ids_defined_including_g5_split():
    assert set(GATES) == {"G0", "G1", "G2", "G3", "G4", "G5a", "G5b", "G6", "G7", "G8", "G9"}


def test_human_gates_are_exactly_the_three_plus_split():
    human = {g for g, spec in GATES.items() if spec["human"]}
    assert human == {"G2", "G5a", "G5b", "G9"}


def test_transitions_reference_only_known_states_and_gates():
    for t in TRANSITIONS:
        assert t["from"] in STATES, t
        assert t["to"] in STATES, t
        assert t["gate"] is None or t["gate"] in GATES, t
        assert t["on_fail"] in {"REWORK", "BLOCKED"}, t


def test_every_nonterminal_state_has_an_exit():
    outgoing = {t["from"] for t in TRANSITIONS}
    for state in STATES - TERMINAL - POLICY_STATES:
        assert state in outgoing, f"state {state} has no outgoing transition (finding 1)"


def test_every_state_is_reachable():
    incoming = {t["to"] for t in TRANSITIONS}
    fail_targets = {t["on_fail"] for t in TRANSITIONS}
    for state in STATES - {"NEW"} - POLICY_STATES:
        assert state in incoming, f"state {state} unreachable"
    assert POLICY_STATES - {"CANCELLED"} <= fail_targets | {"BLOCKED"}
    assert SM["blocked_policy"]["reachable_from"].startswith("any")
    assert SM["cancelled_policy"]["reachable_from"].startswith("any")


def test_every_gate_is_used_by_some_transition():
    used = {t["gate"] for t in TRANSITIONS if t["gate"]}
    assert used == set(GATES), f"gates never used: {set(GATES) - used}"


def test_rework_targets_are_known_states():
    for target in SM["rework_policy"]["default_targets_by_reason_prefix"].values():
        assert target in STATES, target


def test_terminal_states_have_no_exit():
    outgoing = {t["from"] for t in TRANSITIONS}
    assert not (TERMINAL & outgoing)


def test_human_gate_transitions_require_approval_record():
    for t in TRANSITIONS:
        if t["gate"] in {"G2", "G5a", "G5b", "G9"}:
            assert "approval_record" in t["required_artifacts"], t
