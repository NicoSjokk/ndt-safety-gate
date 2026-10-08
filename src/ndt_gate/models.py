"""Data types shared by the agent, the gate and the twin."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ActionType(StrEnum):
    """Orchestration actions the agent may propose."""

    SCALE = "scale"  # change replica count of a deployment
    MIGRATE = "migrate"  # move a deployment's pods to another node
    RECOVER = "recover"  # restart / reschedule a failed function


class Decision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"


@dataclass(frozen=True)
class ProposedAction:
    """A structured action as emitted by the agent (JSON on the wire)."""

    type: ActionType
    namespace: str
    target: str
    params: dict[str, Any] = field(default_factory=dict)
    rationale: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProposedAction:
        missing = {"type", "namespace", "target"} - data.keys()
        if missing:
            raise ValueError(f"action is missing fields: {sorted(missing)}")
        return cls(
            type=ActionType(data["type"]),
            namespace=data["namespace"],
            target=data["target"],
            params=dict(data.get("params", {})),
            rationale=data.get("rationale", ""),
        )


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one gate stage."""

    name: str
    passed: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ServiceMetrics:
    p95_latency_ms: float
    error_rate: float


@dataclass(frozen=True)
class TwinObservation:
    """What the twin measured after applying an action and replaying load."""

    services: dict[str, ServiceMetrics]
    pending_pods: int = 0
    failed_pods: int = 0
    min_node_cpu_headroom: float = 1.0


@dataclass(frozen=True)
class Verdict:
    """The gate's answer, returned to the agent or forwarded to prod."""

    decision: Decision
    action: ProposedAction
    checks: tuple[CheckResult, ...]
    validation_seconds: float

    @property
    def approved(self) -> bool:
        return self.decision is Decision.APPROVE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
