"""Apply actions to the cluster with kubectl."""

import subprocess

from ndt_gate.models import ActionType, ProposedAction


def kubectl_args(action: ProposedAction, namespace: str) -> list[str]:
    """The kubectl command that applies the action in the given namespace."""
    deployment = f"deployment/{action.target}"
    if action.type is ActionType.SCALE:
        replicas = action.params["replicas"]
        return ["kubectl", "scale", deployment, "-n", namespace, f"--replicas={replicas}"]
    if action.type is ActionType.RESIZE:
        cpu = action.params["cpu_limit"]
        return ["kubectl", "set", "resources", deployment, "-n", namespace, f"--limits=cpu={cpu}"]
    raise NotImplementedError(f"'{action.type}' actions are not supported yet")


def apply(action: ProposedAction, namespace: str) -> None:
    subprocess.run(kubectl_args(action, namespace), check=True)
    rollout = ["kubectl", "rollout", "status", f"deployment/{action.target}", "-n", namespace]
    subprocess.run(rollout, check=True)