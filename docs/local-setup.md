# Local setup

How I run the local test cluster on Windows (PowerShell). Everything runs on the laptop in Docker.

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

## 2. Service chain

Two copies of podinfo, where the frontend forwards every request to the backend:

```powershell
helm repo add podinfo https://stefanprodan.github.io/podinfo
kubectl create namespace chain
helm install backend podinfo/podinfo -n chain
helm install frontend podinfo/podinfo -n chain --set backend=http://backend-podinfo:9898/echo
```

## 3. Prometheus

```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
helm upgrade backend podinfo/podinfo -n chain --reuse-values --set serviceMonitor.enabled=true
helm upgrade frontend podinfo/podinfo -n chain --reuse-values --set serviceMonitor.enabled=true
```

Open Prometheus at http://localhost:9090 (keep this running):

```powershell
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

## 4. Load

Runs from inside the cluster, 2 minutes with 10 concurrent users:

```powershell
kubectl run load -n chain --rm -it --restart=Never --image=williamyeh/hey -- -z 2m -c 10 -m POST -d hello http://frontend-podinfo:9898/echo
```

## 5. Read the numbers from Python

With the Prometheus port-forward running:

```powershell
python src\ndt_gate\telemetry.py
```

## Example of a bad change

Limit the backend to 5% of one CPU core, then run the same load again:

```powershell
kubectl set resources deployment backend-podinfo -n chain --limits=cpu=50m
```

To undo it, run `kubectl edit deployment backend-podinfo -n chain` and delete the
`limits:` / `cpu: 50m` lines. (`--limits=cpu=0` is rejected because the chart sets a CPU request.)

First run on 20 Oct 2026: p95 went from 36 ms to 198 ms and throughput from 1120 to 155 req/s,
with zero errors.

## Clean up

```powershell
k3d cluster delete twin
```
