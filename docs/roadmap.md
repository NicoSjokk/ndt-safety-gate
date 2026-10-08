# Roadmap

Plan as of October 2026. Dates move; the order mostly doesn't.

- [x] Gate interface, policy and SLO checks, stub twin, tests, CI
- [ ] Terraform: two local clusters (`prod`, `twin`) with Prometheus and Grafana
- [ ] Service chain deployed to both clusters (real functions instead of placeholders)
- [ ] `KubernetesTwin`: sync from prod, apply action, replay traffic, read PromQL
- [ ] Policy stage moved to Kyverno or OPA/Gatekeeper
- [ ] Scripted agent, then a Python LLM agent emitting structured actions
- [ ] Experiment harness: 30 scenarios × direct vs. gated × 5 repetitions
- [ ] Scenario 2: Open5GS 5G core + UERANSIM on Kubernetes
- [ ] Fault injection with Chaos Mesh
- [ ] Twin fidelity study (predicted vs. real outcome per action type)
- [ ] Larger runs on NTNU infrastructure (IDUN) or a managed cloud cluster

## Scenarios and resources under consideration

- [Open5GS](https://open5gs.org/open5gs/docs/) and [UERANSIM](https://github.com/aligungr/UERANSIM) for the 5G core scenario
- [ns-O-RAN + FlexRIC](https://github.com/Orange-OpenSource/ns-O-RAN-flexric) for a possible RAN-side scenario
- [IDUN](https://www.hpc.ntnu.no/idun/documentation/), NTNU's HPC cluster, for compute-heavy experiment runs
