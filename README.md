# ndt-safety-gate

[![CI](https://github.com/NicoSjokk/ndt-safety-gate/actions/workflows/ci.yml/badge.svg)](https://github.com/NicoSjokk/ndt-safety-gate/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

**Test before execute:** a safety gate for AI-driven network orchestration.
An AI agent proposes an action (scale, migrate, restart a network function).
Before it reaches production, the action runs in a **network digital twin on
Kubernetes**, and it only goes through if the twin shows the SLOs still hold.

Master's thesis project at NTNU (Department of Information Security and
Communication Technology), 2026–2027.

> **Status: early.** The gate logic, its tests and the service chain manifests are
> here. The twin is currently a small stand-in model (`StubTwin`); the real
> Kubernetes twin, the LLM agent and the experiments are next. See the
> [roadmap](docs/roadmap.md).

## How it works

```mermaid
flowchart LR
    T[(Prometheus<br/>telemetry)] --> A[AI agent<br/>LLM, tool calling]
    I[Intent / SLOs] --> A
    A -- proposed action<br/>JSON --> G

    subgraph G[Safety gate]
        direction TB
        P[1 · Policy check<br/>static rules] --> W[2 · Twin test<br/>apply + replay load]
        W --> S[3 · SLO check<br/>target and neighbours]
    end

    W <-. sync state .-> TW[(Twin cluster)]
    S -- approve --> PR[(Prod cluster)]
    S -- reject + reasons --> A
    P -- reject + reasons --> A
    PR -. real outcome vs.<br/>twin prediction .-> F[Fidelity metric]
```

1. **Policy check.** Cheap static rules: protected namespaces, replica bounds, allowed nodes. Forbidden actions never reach the twin.
2. **Twin test.** The twin is synced from prod (replicas, limits, placement, recent traffic), the action is applied, and load is replayed.
3. **SLO check.** p95 latency, error rate, failed or pending pods and CPU headroom, checked for **every** service, so an action that helps its target but starves a neighbour is caught.

More detail in [docs/architecture.md](docs/architecture.md).

## Research questions

- **RQ1.** How can a cloud-native network digital twin act as a pre-execution gate for agent-proposed actions, and where does it fit in the ETSI ZSM closed loop?
- **RQ2.** Compared with direct execution, how much does gating reduce SLA violations and unsafe actions, and how much delay does it add?
- **RQ3.** How accurately does the twin predict the real effect of each action type, and when do fidelity gaps lead to wrong decisions?

## Quick start

```bash
git clone https://github.com/NicoSjokk/ndt-safety-gate.git
cd ndt-safety-gate
python -m venv .venv && source .venv/bin/activate
make install
make test
```

Run an action through the gate (against the stub twin):

```console
$ ndt-gate validate examples/actions/scale-out-safe.json
{ "decision": "approve", ... }

$ ndt-gate validate examples/actions/migrate-to-busy-node.json
{ "decision": "reject",
  "checks": [ ..., { "name": "slo", "passed": false,
                     "reasons": ["node CPU headroom 12% < 20%"] } ], ... }
```

The exit code is `0` for approve and `1` for reject, so the gate can sit in a CI pipeline.

| Example action | Expected | Why |
|---|---|---|
| `scale-out-safe.json` | approve | One extra replica, plenty of capacity |
| `scale-out-starves-neighbour.json` | reject | Fills every node; pods go pending, no headroom left |
| `migrate-to-busy-node.json` | reject | Target node ends up with too little CPU headroom |
| `touch-kube-system.json` | reject | Blocked by policy before the twin is used |
| `recover-crashed-store.json` | approve | Run with `--state examples/cluster-state-store-crashed.json` |

## Repository layout

```
src/ndt_gate/        gate, policy and SLO checks, twin interface + stub, CLI
tests/               pytest suite
examples/            cluster state and example agent actions
deploy/k8s/          service chain manifests (kustomize base + prod/twin overlays)
deploy/terraform/    cluster provisioning (planned)
docs/                architecture and roadmap
```

## Scenarios

1. **Service chain** (`frontend → processor → store`) on Kubernetes. First target; manifests in `deploy/k8s/service-chain`.
2. **5G core**: Open5GS + UERANSIM on Kubernetes. Planned.

Action types: **scale** in/out, **migrate** to another node, **recover** a failed function.

## Planned stack

Kubernetes (kind/k3d locally) · Terraform · Helm · Prometheus/Grafana · Kyverno or OPA · Chaos Mesh · Python LLM agent. Larger runs may use NTNU's IDUN cluster.

## Background

- ETSI GS ZSM 018, network digital twin for zero-touch management
- Raza et al. (2025), survey on network digital twins and AI-driven orchestration

## License

[MIT](LICENSE) © 2026 Nicolai Skjerven
