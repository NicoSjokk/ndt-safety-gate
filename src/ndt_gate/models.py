from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ActionType(StrEnum):
    SCALE = "scale"
    MIGRATE = "migrate"
    RECOVER = "recover"


@dataclass(frozen=True)
class ProposedAction:
    type: ActionType
    namespace: str
    target: str
    params: dict[str, Any] = field(default_factory=dict)

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
        )


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    reasons: tuple[str, ...] = ()
