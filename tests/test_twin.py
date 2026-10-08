from ndt_gate.models import ActionType, ProposedAction
from ndt_gate.twin import StubTwin


def scale(n: int) -> ProposedAction:
    return ProposedAction(ActionType.SCALE, "service-chain", "processor", {"replicas": n})


def test_twin_does_not_mutate_prod(prod_state):
    twin = StubTwin(prod_state)
    twin.apply_and_observe(scale(6))
    assert prod_state.deployments["processor"].replicas == 3


def test_sync_resets_twin_to_prod(prod_state):
    twin = StubTwin(prod_state)
    twin.apply_and_observe(scale(6))
    twin.sync_from_prod()
    assert twin.state.deployments["processor"].replicas == 3


def test_scale_out_lowers_latency(prod_state):
    twin = StubTwin(prod_state)
    before = twin.observe().services["processor"].p95_latency_ms
    after = twin.apply_and_observe(scale(4)).services["processor"].p95_latency_ms
    assert after < before


def test_overscaling_leaves_pods_pending(prod_state):
    obs = StubTwin(prod_state).apply_and_observe(scale(10))
    assert obs.pending_pods > 0
    assert obs.min_node_cpu_headroom == 0


def test_scale_in_removes_replicas(prod_state):
    twin = StubTwin(prod_state)
    twin.apply_and_observe(scale(1))
    assert twin.state.deployments["processor"].replicas == 1
