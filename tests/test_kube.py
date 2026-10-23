from ndt_gate.kube import kubectl_args
from ndt_gate.models import ProposedAction
from ndt_gate.kube import undo_args

def test_resize_runs_in_the_namespace_we_ask_for():
    action = ProposedAction.from_dict(
        {"type": "resize", "namespace": "prod", "target": "backend-podinfo",
         "params": {"cpu_limit": "50m"}}
    )
    assert kubectl_args(action, "twin") == [
        "kubectl", "set", "resources", "deployment/backend-podinfo",
        "-n", "twin", "--limits=cpu=50m",
    ]

def test_resize_is_undone_with_a_rollout_undo():
    action = ProposedAction.from_dict(
        {"type": "resize", "namespace": "prod", "target": "backend-podinfo",
         "params": {"cpu_limit": "50m"}}
    )
    assert undo_args(action, "twin") == [
        "kubectl", "rollout", "undo", "deployment/backend-podinfo", "-n", "twin",
    ]