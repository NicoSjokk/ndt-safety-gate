"""The test-before-execute gate: policy check -> twin test -> SLO check."""

from __future__ import annotations

import time

from ndt_gate.models import CheckResult, Decision, ProposedAction, Verdict
from ndt_gate.policy import PolicyConfig, check_policy
from ndt_gate.slo import SLO, check_slo
from ndt_gate.twin import Twin


class Gate:
    def __init__(
        self,
        twin: Twin,
        policy: PolicyConfig | None = None,
        slo: SLO | None = None,
        observe_seconds: float = 60.0,
    ) -> None:
        self.twin = twin
        self.policy = policy or PolicyConfig()
        self.slo = slo or SLO()
        self.observe_seconds = observe_seconds

    def validate(self, action: ProposedAction) -> Verdict:
        start = time.perf_counter()
        checks: list[CheckResult] = []

        policy_result = check_policy(action, self.policy)
        checks.append(policy_result)
        if not policy_result.passed:
            # Fail fast: no point spending twin time on a forbidden action.
            return self._verdict(Decision.REJECT, action, checks, start)

        self.twin.sync_from_prod()
        try:
            obs = self.twin.apply_and_observe(action, self.observe_seconds)
        except (KeyError, ValueError) as exc:
            checks.append(CheckResult(name="twin", passed=False, reasons=(str(exc),)))
            return self._verdict(Decision.REJECT, action, checks, start)
        checks.append(CheckResult(name="twin", passed=True))

        slo_result = check_slo(obs, self.slo)
        checks.append(slo_result)
        decision = Decision.APPROVE if slo_result.passed else Decision.REJECT
        return self._verdict(decision, action, checks, start)

    @staticmethod
    def _verdict(
        decision: Decision, action: ProposedAction, checks: list[CheckResult], start: float
    ) -> Verdict:
        return Verdict(
            decision=decision,
            action=action,
            checks=tuple(checks),
            validation_seconds=time.perf_counter() - start,
        )
