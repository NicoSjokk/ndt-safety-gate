import json

import pytest

from ndt_gate import Decision, Gate, ProposedAction
from ndt_gate.cli import main
from ndt_gate.twin import ClusterState, StubTwin


class ExplodingTwin:
    """Fails the test if the gate touches the twin."""

    def sync_from_prod(self):
        raise AssertionError("twin should not be used")

    def apply_and_observe(self, action, duration_s):
        raise AssertionError("twin should not be used")


def load(examples, name) -> ProposedAction:
    return ProposedAction.from_dict(json.loads((examples / "actions" / name).read_text()))


@pytest.mark.parametrize(
    ("action_file", "expected"),
    [
        ("scale-out-safe.json", Decision.APPROVE),
        ("scale-out-starves-neighbour.json", Decision.REJECT),
        ("migrate-to-busy-node.json", Decision.REJECT),
        ("touch-kube-system.json", Decision.REJECT),
    ],
)
def test_example_actions(examples, prod_state, action_file, expected):
    verdict = Gate(StubTwin(prod_state)).validate(load(examples, action_file))
    assert verdict.decision is expected


def test_recover_fixes_crashed_function(examples):
    state = ClusterState.load(examples / "cluster-state-store-crashed.json")
    verdict = Gate(StubTwin(state)).validate(load(examples, "recover-crashed-store.json"))
    assert verdict.approved


def test_policy_rejection_skips_twin(examples):
    verdict = Gate(ExplodingTwin()).validate(load(examples, "touch-kube-system.json"))
    assert verdict.decision is Decision.REJECT
    assert [c.name for c in verdict.checks] == ["policy"]


def test_unknown_target_is_rejected(prod_state):
    action = ProposedAction.from_dict(
        {"type": "recover", "namespace": "service-chain", "target": "does-not-exist"}
    )
    verdict = Gate(StubTwin(prod_state)).validate(action)
    assert not verdict.approved
    assert verdict.checks[-1].name == "twin"


def test_verdict_records_validation_time(examples, prod_state):
    verdict = Gate(StubTwin(prod_state)).validate(load(examples, "scale-out-safe.json"))
    assert verdict.validation_seconds >= 0


def test_cli_exit_codes(examples, capsys):
    state = str(examples / "cluster-state.json")
    assert main(["validate", str(examples / "actions/scale-out-safe.json"), "--state", state]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "approve"
    bad = str(examples / "actions/migrate-to-busy-node.json")
    assert main(["validate", bad, "--state", state]) == 1
