"""Stage 2: run the action in the network digital twin.

`Twin` is the interface the gate depends on. The real implementation (planned)
syncs a second Kubernetes cluster from prod, applies the action there, replays
recent traffic and reads the result from Prometheus.

`StubTwin` is a small analytical stand-in used for tests and for developing the
gate before the clusters exist. It is a toy capacity model, not a claim about
how real services behave; measuring how well the *real* twin predicts prod is
part of the thesis (RQ3).
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ndt_gate.models import ActionType, ProposedAction, ServiceMetrics, TwinObservation


class Twin(Protocol):
    def sync_from_prod(self) -> None:
        """Copy prod's current state (replicas, limits, placement, traffic) into the twin."""

    def apply_and_observe(self, action: ProposedAction, duration_s: float) -> TwinObservation:
        """Apply the action in the twin, replay load for `duration_s`, return what was seen."""


@dataclass
class Deployment:
    rps: float  # offered load
    rps_per_replica: float  # capacity of one replica
    cpu_per_replica: float  # cores requested per replica
    base_latency_ms: float  # latency at zero load
    placement: dict[str, int] = field(default_factory=dict)  # node -> replicas
    crashed: int = 0  # replicas currently in a failed state

    @property
    def replicas(self) -> int:
        return sum(self.placement.values())


@dataclass
class ClusterState:
    nodes: dict[str, float]  # node -> CPU cores
    deployments: dict[str, Deployment]
    pending: int = 0

    @classmethod
    def from_dict(cls, data: dict) -> ClusterState:
        return cls(
            nodes={k: float(v) for k, v in data["nodes"].items()},
            deployments={k: Deployment(**v) for k, v in data["deployments"].items()},
        )

    @classmethod
    def load(cls, path: str | Path) -> ClusterState:
        return cls.from_dict(json.loads(Path(path).read_text()))

    def node_used(self, node: str) -> float:
        return sum(d.cpu_per_replica * d.placement.get(node, 0) for d in self.deployments.values())

    def node_free(self, node: str) -> float:
        return self.nodes[node] - self.node_used(node)


# Latency multiplier once a node is busier than this.
_CONTENTION_START = 0.8


class StubTwin:
    """In-memory toy twin. Deterministic, no cluster needed."""

    def __init__(self, prod: ClusterState) -> None:
        self._prod = prod
        self.state = copy.deepcopy(prod)

    def sync_from_prod(self) -> None:
        self.state = copy.deepcopy(self._prod)

    def apply_and_observe(
        self, action: ProposedAction, duration_s: float = 60.0
    ) -> TwinObservation:
        dep = self.state.deployments.get(action.target)
        if dep is None:
            raise KeyError(f"unknown deployment '{action.target}'")

        if action.type is ActionType.SCALE:
            self._scale(dep, int(action.params["replicas"]))
        elif action.type is ActionType.MIGRATE:
            self._migrate(dep, str(action.params["to_node"]))
        elif action.type is ActionType.RECOVER:
            dep.crashed = 0

        return self.observe()

    def observe(self) -> TwinObservation:
        s = self.state
        util = {n: s.node_used(n) / cap for n, cap in s.nodes.items()}
        services = {name: self._metrics(d, util) for name, d in s.deployments.items()}
        return TwinObservation(
            services=services,
            pending_pods=s.pending,
            failed_pods=sum(d.crashed for d in s.deployments.values()),
            min_node_cpu_headroom=min(1.0 - u for u in util.values()),
        )

    # -- action effects -------------------------------------------------

    def _place_one(self, dep: Deployment) -> None:
        node = max(self.state.nodes, key=self.state.node_free)
        if self.state.node_free(node) >= dep.cpu_per_replica:
            dep.placement[node] = dep.placement.get(node, 0) + 1
        else:
            self.state.pending += 1

    def _scale(self, dep: Deployment, replicas: int) -> None:
        while dep.replicas < replicas:
            before = dep.replicas
            self._place_one(dep)
            if dep.replicas == before:  # did not fit; the rest stay pending too
                self.state.pending += replicas - dep.replicas - 1
                break
        while dep.replicas > replicas:
            node = max(dep.placement, key=dep.placement.__getitem__)
            dep.placement[node] -= 1

    def _migrate(self, dep: Deployment, to_node: str) -> None:
        moving = dep.replicas
        dep.placement = {}
        if to_node not in self.state.nodes:
            self.state.pending += moving
            return
        fits = int(self.state.node_free(to_node) // dep.cpu_per_replica)
        dep.placement[to_node] = min(moving, fits)
        self.state.pending += max(0, moving - fits)

    # -- metrics --------------------------------------------------------

    @staticmethod
    def _metrics(dep: Deployment, util: dict[str, float]) -> ServiceMetrics:
        running = dep.replicas - dep.crashed
        if running <= 0:
            return ServiceMetrics(p95_latency_ms=10_000.0, error_rate=1.0)

        contention = sum(
            count * (1 + 5 * max(0.0, util[node] - _CONTENTION_START))
            for node, count in dep.placement.items()
        ) / max(dep.replicas, 1)

        load = dep.rps / (running * dep.rps_per_replica)
        if load >= 1.0:
            return ServiceMetrics(
                p95_latency_ms=dep.base_latency_ms * contention / 0.05,
                error_rate=1.0 - 1.0 / load,
            )
        return ServiceMetrics(
            p95_latency_ms=dep.base_latency_ms * contention / (1.0 - load),
            error_rate=0.0,
        )
