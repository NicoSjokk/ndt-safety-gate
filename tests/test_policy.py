import pytest

from ndt_gate.models import ActionType, ProposedAction
from ndt_gate.policy import PolicyConfig, check_policy


def action(**kw) -> ProposedAction:
    base = dict(type=ActionType.SCALE, namespace="default", target="web", params={"replicas": 3})
    base.update(kw)
    return ProposedAction(**base)


def test_valid_scale_passes():
    assert check_policy(action(), PolicyConfig()).passed


def test_protected_namespace_is_rejected():
    assert not check_policy(action(namespace="kube-system"), PolicyConfig()).passed


@pytest.mark.parametrize("replicas", [0, 11, "3", None])
def test_bad_replicas_are_rejected(replicas):
    assert not check_policy(action(params={"replicas": replicas}), PolicyConfig()).passed


def test_migrate_needs_target_node():
    assert not check_policy(action(type=ActionType.MIGRATE, params={}), PolicyConfig()).passed


def test_from_dict_requires_fields():
    with pytest.raises(ValueError, match="missing"):
        ProposedAction.from_dict({"type": "scale"})
