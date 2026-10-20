import sys

import requests

PROM = "http://localhost:9090"


def query(promql):
    r = requests.get(f"{PROM}/api/v1/query", params={"query": promql}, timeout=10)
    r.raise_for_status()
    return {s["metric"].get("job", "?"): float(s["value"][1]) for s in r.json()["data"]["result"]}


def p95_latency(namespace, window="1m"):
    return query(
        "histogram_quantile(0.95, sum by (le, job) "
        f'(rate(http_request_duration_seconds_bucket{{namespace="{namespace}"}}[{window}])))'
    )


def error_rate(namespace, window="1m"):
    count = "http_request_duration_seconds_count"
    total = query(f'sum by (job) (rate({count}{{namespace="{namespace}"}}[{window}]))')
    errors = query(
        f'sum by (job) (rate({count}{{namespace="{namespace}", status=~"5.."}}[{window}]))'
    )
    return {job: errors.get(job, 0.0) / rate for job, rate in total.items() if rate > 0}


if __name__ == "__main__":
    namespace = sys.argv[1] if len(sys.argv) > 1 else "prod"
    print(f"[{namespace}] p95 latency (s):", p95_latency(namespace))
    print(f"[{namespace}] error rate:", error_rate(namespace))