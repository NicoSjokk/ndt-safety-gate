"""Stage 1: static policy check.

Cheap rules evaluated before anything touches the twin. In the full system these
move to policy-as-code (Kyverno or OPA/Gatekeeper); this module mirrors the same
rules in Python so the gate can be tested without a cluster.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ndt_gate.models import ActionType, CheckResult, ProposedAction


@dataclass(frozen=True)
class PolicyConfig:
    min_replicas: int = 1
    max_replicas: int = 10
    protected_namespaces: frozenset[str] = field(
        default_factory=lambda: frozenset({"kube-system", "monitoring", "argocd"})
    )
    allowed_nodes: frozenset[str] | None = None  # None = any node


def check_policy(action: ProposedAction, config: PolicyConfig) -> CheckResult:
    reasons: list[str] = []

    if action.namespace in config.protected_namespaces:
        reasons.append(f"namespace '{action.namespace}' is protected")

    if action.type is ActionType.SCALE:
        replicas = action.params.get("replicas")
        if not isinstance(replicas, int):
            reasons.append("scale action needs an integer 'replicas' param")
        elif not config.min_replicas <= replicas <= config.max_replicas:
            reasons.append(
                f"replicas={replicas} outside allowed range "
                f"[{config.min_replicas}, {config.max_replicas}]"
            )

    if action.type is ActionType.MIGRATE:
        node = action.params.get("to_node")
        if not node:
            reasons.append("migrate action needs a 'to_node' param")
        elif config.allowed_nodes is not None and node not in config.allowed_nodes:
            reasons.append(f"node '{node}' is not an allowed target")

    return CheckResult(name="policy", passed=not reasons, reasons=tuple(reasons))
