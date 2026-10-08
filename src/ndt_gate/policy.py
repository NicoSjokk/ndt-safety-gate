"""Static policy check, run before an action is tried in the twin."""

from __future__ import annotations

from dataclasses import dataclass, field

from ndt_gate.models import ActionType, CheckResult, ProposedAction


@dataclass(frozen=True)
class PolicyConfig:
    min_replicas: int = 1
    max_replicas: int = 10
    protected_namespaces: frozenset[str] = field(
        default_factory=lambda: frozenset({"kube-system", "monitoring"})
    )


def check_policy(action: ProposedAction, config: PolicyConfig) -> CheckResult:
    reasons: list[str] = []

    if action.namespace in config.protected_namespaces:
        reasons.append(f"namespace '{action.namespace}' is protected")

    if action.type is ActionType.SCALE:
        replicas = action.params.get("replicas")
        if not isinstance(replicas, int):
            reasons.append("scale action needs an integer 'replicas' param")
        elif not config.min_replicas <= replicas <= config.max_replicas:
            reasons.append(f"replicas={replicas} is outside the allowed range")

    if action.type is ActionType.MIGRATE and not action.params.get("to_node"):
        reasons.append("migrate action needs a 'to_node' param")

    return CheckResult(name="policy", passed=not reasons, reasons=tuple(reasons))
