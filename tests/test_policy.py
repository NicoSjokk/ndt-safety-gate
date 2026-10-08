import pytest

from ndt_gate.models import ActionType, ProposedAction
from ndt_gate.policy import PolicyConfig, check_policy


def action(**kw) -> ProposedAction:
    base = dict(
        type=ActionType.SCALE, namespace="service-chain", target="processor", params={"replicas": 3}
    )
    base.update(kw)
    return ProposedAction(**base)


def test_valid_scale_passes():
    assert check_policy(action(), PolicyConfig()).passed


def test_protected_namespace_is_rejected():
    result = check_policy(action(namespace="kube-system"), PolicyConfig())
    assert not result.passed
    assert "protected" in result.reasons[0]


@pytest.mark.parametrize("replicas", [0, 11, "3", None])
def test_replicas_out_of_range_or_wrong_type(replicas):
    assert not check_policy(action(params={"replicas": replicas}), PolicyConfig()).passed


def test_migrate_needs_target_node():
    a = action(type=ActionType.MIGRATE, params={})
    assert not check_policy(a, PolicyConfig()).passed


def test_migrate_to_disallowed_node():
    a = action(type=ActionType.MIGRATE, params={"to_node": "edge-9"})
    cfg = PolicyConfig(allowed_nodes=frozenset({"worker-1", "worker-2"}))
    assert not check_policy(a, cfg).passed


def test_action_from_dict_requires_fields():
    with pytest.raises(ValueError, match="missing"):
        ProposedAction.from_dict({"type": "scale"})
