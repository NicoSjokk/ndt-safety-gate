# Local setup

How I run the local test cluster on Windows (PowerShell). Everything runs on the laptop in Docker.

The service chain runs twice: `prod` plays the live system and `twin` is the copy where changes
are tested first.

## Tools

```powershell
winget install Docker.DockerDesktop
winget install k3d.k3d
winget install Kubernetes.kubectl
winget install Helm.Helm
```

Start Docker Desktop before the steps below.

## 1. Cluster

One server node and two worker nodes:

```powershell
k3d cluster create twin --agents 2
kubectl get nodes
```

## 2. Prometheus

```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add podinfo https://stefanprodan.github.io/podinfo
helm repo update
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

Open Prometheus at http://localhost:9090 (keep this running):

```powershell
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

## 3. Service chain, prod and twin

Two copies of podinfo in each namespace, where the frontend forwards every request to the backend
in the same namespace:

```powershell
foreach ($ns in "prod", "twin") {
  kubectl create namespace $ns
  helm install backend podinfo/podinfo -n $ns --set serviceMonitor.enabled=true
  helm install frontend podinfo/podinfo -n $ns --set backend=http://backend-podinfo:9898/echo --set serviceMonitor.enabled=true
}
```

## 4. Load

Steady "real user" traffic on prod, 100 req/s for 30 minutes (leave it running):

```powershell
kubectl run load-prod -n prod --rm -it --restart=Never --image=williamyeh/hey -- -z 30m -c 5 -q 20 -m POST -d hello http://frontend-podinfo:9898/echo
```

The same traffic on the twin, for 2 minutes per test:

```powershell
kubectl run load-twin -n twin --rm -it --restart=Never --image=williamyeh/hey -- -z 2m -c 5 -q 20 -m POST -d hello http://frontend-podinfo:9898/echo
```

Let a run finish on its own. Stopping it with Ctrl+C can leave the pod behind, and the next run
then fails because the name is taken.

## 5. Read the numbers from Python

With the Prometheus port-forward running, inside the venv:

```powershell
python src/ndt_gate/telemetry.py prod
python src/ndt_gate/telemetry.py twin
```

## Example: test a bad change on the twin

Limit the twin backend to 5% of one CPU core, then run `load-twin` again and check both namespaces:

```powershell
kubectl set resources deployment backend-podinfo -n twin --limits=cpu=50m
kubectl rollout status deployment backend-podinfo -n twin
```

To undo it, run `kubectl edit deployment backend-podinfo -n twin` and delete the
`limits:` / `cpu: 50m` lines. (`--limits=cpu=0` is rejected because the chart sets a CPU request.)

Result on 20 Oct 2026, at 100 req/s: twin frontend p95 went from 4.8 ms to 70 ms with zero
errors, while prod stayed at 4.75 ms. `slo.py` flags this, since p95 more than doubled.

Note: all four podinfo pods ended up on the same worker node, so prod and twin share CPU. A heavy
twin test can slow prod down.

## Clean up

```powershell
k3d cluster stop twin     # pause, start again with: k3d cluster start twin
k3d cluster delete twin   # remove everything
```
