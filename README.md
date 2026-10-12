# ndt-safety-gate

Master's thesis project at NTNU (2026–2027).

An AI agent that manages a network should not change production directly. This project is about
testing its proposed actions (scale, migrate, recover) in a network digital twin first, and only
letting them through if the service levels still hold.

Work in progress. Right now there is only the action format and a first static policy check.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
