FLOOR = 0.005  # smallest podinfo latency bucket; below this Prometheus can't tell values apart


def check_p95(before, after, max_ratio=2.0):
    """Return the services whose p95 got more than max_ratio times worse."""
    worse = {}
    for job, old in before.items():
        new = after.get(job)
        if new is not None and new > max(old, FLOOR) * max_ratio:
            worse[job] = (old, new)
    return worse