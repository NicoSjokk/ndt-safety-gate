# Terraform (planned)

Will provision the two environments the gate needs:

- `prod`: the cluster the agent is trying to manage
- `twin`: a clone of `prod`, built from the same manifests, where actions are tested first

Local first (kind or k3d via the Terraform kind/helm providers), with Prometheus
and Grafana installed by Helm. One optional run on a managed cloud cluster at the
end. Nothing here yet.
