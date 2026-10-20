from ndt_gate.slo import check_p95

BEFORE = {"frontend-podinfo": 0.0048, "backend-podinfo": 0.00475}


def test_cpu_limit_on_twin_is_caught():
    after = {"frontend-podinfo": 0.0704, "backend-podinfo": 0.00477}
    assert check_p95(BEFORE, after) == {"frontend-podinfo": (0.0048, 0.0704)}


def test_noise_near_the_bucket_floor_is_ignored():
    after = {"frontend-podinfo": 0.0049, "backend-podinfo": 0.0048}
    assert check_p95(BEFORE, after) == {}