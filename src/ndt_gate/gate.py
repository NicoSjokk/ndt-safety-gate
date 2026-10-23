"""Run one proposed action through the gate: policy check, twin test, then prod or rollback."""

import json
import sys
import time

from ndt_gate import kube, telemetry
from ndt_gate.models import ProposedAction
from ndt_gate.policy import PolicyConfig, check_policy
from ndt_gate.slo import check_p95, ratios

TWIN = "twin"
SETTLE_SECONDS = 90  # Prometheus averages over the last minute, so wait a bit longer than that


def run(action: ProposedAction) -> bool:
    policy = check_policy(action, PolicyConfig())
    if not policy.passed:
        print("BLOCKED by policy:", "; ".join(policy.reasons))
        return False

    before = telemetry.p95_latency(TWIN)
    print("twin p95 before:", before)

    kube.apply(action, TWIN)
    print(f"applied to twin, waiting {SETTLE_SECONDS}s for new numbers...")
    time.sleep(SETTLE_SECONDS)

    after = telemetry.p95_latency(TWIN)
    print("twin p95 after:", after)

    worse = check_p95(before, after)
    if worse:
        print("BLOCKED, p95 got worse on the twin:", worse)
        kube.undo(action, TWIN)
        print("twin rolled back")
        return False

    print(f"PASSED on the twin, applying to {action.namespace}")
    
    prod_before = telemetry.p95_latency(action.namespace)
    kube.apply(action, action.namespace)
    print(f"applied to {action.namespace}, waiting {SETTLE_SECONDS}s to check it...")
    time.sleep(SETTLE_SECONDS)
    prod_after = telemetry.p95_latency(action.namespace)

    print("predicted change (twin):", ratios(before, after))
    print("actual change (prod):   ", ratios(prod_before, prod_after))

    if check_p95(prod_before, prod_after):
        print("prod got worse even though the twin passed, rolling prod back")
        kube.undo(action, action.namespace)
        return False
    return True


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        action = ProposedAction.from_dict(json.load(f))
    sys.exit(0 if run(action) else 1)