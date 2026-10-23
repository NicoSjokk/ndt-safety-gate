# ndt-safety-gate

An AI agent that manages a network should not change production directly. This project is about
testing its proposed actions (scale, migrate, recover) in a network digital twin first, and only
letting them through if the service levels still hold.

Work in progress. Right now there is the action format, a first static policy check, and a
small telemetry module that reads p95 latency and error rate per service from Prometheus.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
```

For the local test cluster (k3d, a small service chain and Prometheus), see
[docs/local-setup.md](docs/local-setup.md).
