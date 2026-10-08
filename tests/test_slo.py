from ndt_gate.models import ServiceMetrics, TwinObservation
from ndt_gate.slo import SLO, check_slo


def obs(**kw) -> TwinObservation:
    base = dict(
        services={"a": ServiceMetrics(50, 0.0), "b": ServiceMetrics(80, 0.0)},
        min_node_cpu_headroom=0.5,
    )
    base.update(kw)
    return TwinObservation(**base)


def test_healthy_observation_passes():
    assert check_slo(obs(), SLO()).passed


def test_neighbour_violation_counts():
    o = obs(services={"a": ServiceMetrics(50, 0.0), "neighbour": ServiceMetrics(450, 0.0)})
    result = check_slo(o, SLO())
    assert not result.passed
    assert result.reasons[0].startswith("neighbour")


def test_error_rate_threshold_is_exclusive():
    o = obs(services={"a": ServiceMetrics(50, 0.01)})
    assert not check_slo(o, SLO(max_error_rate=0.01)).passed


def test_low_headroom_and_bad_pods_are_reported():
    result = check_slo(obs(min_node_cpu_headroom=0.1, pending_pods=2, failed_pods=1), SLO())
    assert len(result.reasons) == 3
