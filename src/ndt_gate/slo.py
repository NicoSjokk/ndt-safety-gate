"""Stage 3: SLO and side-effect check on what the twin observed."""

from __future__ import annotations

from dataclasses import dataclass

from ndt_gate.models import CheckResult, TwinObservation


@dataclass(frozen=True)
class SLO:
    """Starting thresholds; tuned per scenario in the experiments."""

    p95_latency_ms: float = 200.0
    max_error_rate: float = 0.01
    min_cpu_headroom: float = 0.20


def check_slo(obs: TwinObservation, slo: SLO) -> CheckResult:
    reasons: list[str] = []

    # Every service is checked, not only the target, so side effects on
    # neighbours count as violations.
    for name, m in sorted(obs.services.items()):
        if m.p95_latency_ms > slo.p95_latency_ms:
            reasons.append(
                f"{name}: p95 latency {m.p95_latency_ms:.0f} ms > {slo.p95_latency_ms:.0f} ms"
            )
        if m.error_rate >= slo.max_error_rate:
            reasons.append(f"{name}: error rate {m.error_rate:.1%} >= {slo.max_error_rate:.1%}")

    if obs.pending_pods:
        reasons.append(f"{obs.pending_pods} pod(s) could not be scheduled")
    if obs.failed_pods:
        reasons.append(f"{obs.failed_pods} pod(s) in a failed state")
    if obs.min_node_cpu_headroom < slo.min_cpu_headroom:
        reasons.append(
            f"node CPU headroom {obs.min_node_cpu_headroom:.0%} < {slo.min_cpu_headroom:.0%}"
        )

    return CheckResult(name="slo", passed=not reasons, reasons=tuple(reasons))
