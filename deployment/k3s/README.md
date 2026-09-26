# Beamdata Image Generation — k3s Deployment

This directory contains the **Plan B** Kubernetes deployment for the Beamdata Image Generation project.

> **Plan A remains Docker Compose.**
>
> The k3s manifests are a second deployment path used to validate more production-oriented infrastructure behavior: GPU-aware scheduling, service discovery, secrets, rollout control, ingress, monitoring, and network policy.

---

## 1. Current Architecture

```text
AIDC private network
        |
        |  Node: aidc-t09 / 10.0.0.144
        |
   Traefik Ingress
        |
        +----------------------+
        |                      |
   Gradio Service         Monitoring
        |               Prometheus + Grafana
        |
   Gradio Pod
      /    \
     /      \
FLUX Service  Z-Image Service
    |             |
FLUX Pod       Z-Image Pod
     \           /
      \         /
       RTX A6000 48 GB
       NVIDIA time-slicing
```

### Current workloads

Namespace `beamdata`:

- `flux2-klein`
- `z-image-turbo`
- `gradio`

Namespace `monitoring`:

- `prometheus`
- `grafana`

---

## 2. What k3s Adds Compared with Docker Compose

Docker Compose is still a valid and simpler single-node baseline.

k3s adds:

- Kubernetes Deployments and desired-state reconciliation
- Stable Services and internal DNS
- Namespaces
- Kubernetes Secrets references
- GPU resource scheduling through the NVIDIA device plugin
- GPU time-slicing configuration
- Controlled rollout strategy for GPU workloads
- Traefik Ingress
- NetworkPolicy resources
- Prometheus and Grafana as cluster workloads
- A cleaner path to future multi-node or multi-replica deployment

k3s does **not** automatically provide:

- More GPU capacity
- VRAM isolation
- Lower inference latency
- A public Internet IP
- Useful autoscaling when no additional GPU capacity exists
- High availability on a single-node cluster

---

## 3. Hardware and Environment

Current development node:

- Node: `aidc-t09`
- Private node IP: `10.0.0.144`
- GPU: NVIDIA RTX A6000
- VRAM: ~48 GB
- k3s: single-node cluster
- Traefik: enabled
- NVIDIA device plugin: enabled
- GPU time-slicing: configured with 2 logical GPU replicas

Important:

> NVIDIA time-slicing is **scheduler sharing**, not VRAM isolation.

Both models can coexist on the GPU, but simultaneous generation must still be benchmarked for latency, throughput, failures, and peak VRAM.

---

## 4. Directory Layout

```text
deployment/k3s/
├── frontend/
│   ├── gradio-deployment.yaml
│   └── gradio-service.yaml
├── gpu-sharing/
│   ├── README.md
│   ├── nvidia-device-plugin-patch.yaml
│   └── nvidia-time-slicing-configmap.yaml
├── ingress/
│   └── gradio-ingress.yaml
├── models/
│   ├── flux-deployment.yaml
│   ├── flux-service.yaml
│   ├── namespace.yaml
│   ├── zimage-deployment.yaml
│   └── zimage-service.yaml
├── monitoring/
│   ├── grafana-dashboard-configmap.yaml
│   ├── grafana-dashboard-provider-configmap.yaml
│   ├── grafana-datasource-configmap.yaml
│   ├── grafana-deployment.yaml
│   ├── grafana-service.yaml
│   ├── namespace.yaml
│   ├── prometheus-configmap.yaml
│   ├── prometheus-deployment.yaml
│   └── prometheus-service.yaml
├── network-policy/
│   └── model-network-policy.yaml
├── DEPLOYMENT-TROUBLESHOOTING-REPORT.md
└── verify.sh
```

---

## 5. Required Kubernetes Secrets

The manifests reference Kubernetes Secrets but do not store secret values in Git.

Expected secrets:

### `beamdata/model-tokens`

Keys:

- `flux-token`
- `zimage-token`

### `beamdata/ghcr-pull`

Used as an `imagePullSecret` for private GHCR images.

### `monitoring/grafana-admin`

Keys:

- `admin-user`
- `admin-password`

Verify secret names only:

```bash
kubectl get secrets -n beamdata
kubectl get secrets -n monitoring
```

Do not commit token or password values.

---

## 6. Recommended Deployment Order

### Step 1 — Namespace

```bash
kubectl apply -f deployment/k3s/models/namespace.yaml
kubectl apply -f deployment/k3s/monitoring/namespace.yaml
```

### Step 2 — GPU time-slicing

```bash
kubectl apply -f deployment/k3s/gpu-sharing/nvidia-time-slicing-configmap.yaml
```

The file:

```text
deployment/k3s/gpu-sharing/nvidia-device-plugin-patch.yaml
```

is a **patch file**, not a standalone Kubernetes resource. Do not run:

```bash
kubectl apply -f deployment/k3s/gpu-sharing/nvidia-device-plugin-patch.yaml
```

Use the patch command documented in `deployment/k3s/gpu-sharing/README.md`.

Verify:

```bash
kubectl get node aidc-t09 \
  -o jsonpath='{.status.capacity.nvidia\.com/gpu}{" capacity\n"}{.status.allocatable.nvidia\.com/gpu}{" allocatable\n"}'
```

Expected logical capacity after time-slicing:

```text
2 capacity
2 allocatable
```

### Step 3 — Model workloads

```bash
kubectl apply -f deployment/k3s/models/flux-service.yaml
kubectl apply -f deployment/k3s/models/flux-deployment.yaml
kubectl apply -f deployment/k3s/models/zimage-service.yaml
kubectl apply -f deployment/k3s/models/zimage-deployment.yaml
```

### Step 4 — Gradio

The k3s Gradio image is kept separate from Docker Compose:

```text
beamdata-model-lab-gradio:k3s
```

Build with the **app directory as the build context**:

```bash
docker build \
  -t beamdata-model-lab-gradio:k3s \
  -f app/Dockerfile \
  ./app
```

Import into k3s/containerd:

```bash
docker save beamdata-model-lab-gradio:k3s | \
sudo k3s ctr -n k8s.io images import -
```

Apply:

```bash
kubectl apply -f deployment/k3s/frontend/gradio-service.yaml
kubectl apply -f deployment/k3s/frontend/gradio-deployment.yaml
```

### Step 5 — Monitoring

```bash
kubectl apply -f deployment/k3s/monitoring/
```

### Step 6 — Ingress

```bash
kubectl apply -f deployment/k3s/ingress/gradio-ingress.yaml
```

### Step 7 — NetworkPolicy

Apply network policy **after** core connectivity has been verified:

```bash
kubectl apply -f deployment/k3s/network-policy/model-network-policy.yaml
```

---

## 7. GPU Rollout Strategy

The model Deployments use:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 0
    maxUnavailable: 1
```

Why:

The cluster exposes only 2 logical GPU slots. The Kubernetes default rolling update may try to create a third GPU-consuming pod before terminating the old pod.

That new pod can remain `Pending` because no GPU slot is available.

`maxSurge: 0` prevents that extra GPU pod from being scheduled.

Trade-off:

- safer rollout on constrained GPU capacity
- brief service interruption during a model update is possible

For the current capstone, this trade-off is acceptable.

---

## 8. Gradio Root Path

The application supports an environment-specific root path:

```python
root_path=os.getenv("GRADIO_ROOT_PATH", "/proxy/7860")
```

Docker Compose can continue using the default behavior.

The k3s Deployment can override the path with:

```yaml
- name: GRADIO_ROOT_PATH
  value: "/proxy/80/proxy/7860"
```

This was required because the AIDC IDE adds an additional proxy prefix before traffic reaches Traefik.

---

## 9. Ingress vs Public Internet Access

The k3s Ingress is working, but the node does not have a public Internet IP.

Current network evidence:

```text
Node IP:          10.0.0.144
Traefik external: 10.0.0.144
Ingress address:  10.0.0.144
```

`10.0.0.144` is a private address.

Therefore:

```text
Internet
   |
   |  platform public endpoint / tunnel required
   v
Traefik Ingress
   |
Gradio
```

Ingress provides routing **inside the deployment architecture**. It does not create a public IP by itself.

Public access requires one of:

- AIDC-managed public endpoint
- public IP / NAT / load balancer provided by the infrastructure owner
- a tunnel for temporary demos

This is an infrastructure perimeter limitation, not a k3s deployment failure.

---

## 10. Verification

Run:

```bash
bash deployment/k3s/verify.sh
```

The script checks:

- cluster access
- `beamdata` workloads
- monitoring workloads
- Services
- Ingress
- GPU logical capacity
- current GPU processes / VRAM
- model health from the Gradio pod
- local Traefik route
- NetworkPolicy resources
- disk usage
- YAML client-side validation

---

## 11. Current Validated State

Validated during deployment:

- FLUX and Z-Image can coexist on one RTX A6000
- FLUX health endpoint returns HTTP 200
- Z-Image health endpoint returns HTTP 200
- Gradio can reach both model Services
- real FLUX generation succeeded through the Gradio service layer
- real Z-Image generation succeeded through the Gradio service layer
- Prometheus and Grafana are running
- Prometheus targets were verified UP
- Traefik Ingress returns HTTP 200 from the node
- NetworkPolicy application did not break required allowed paths

Observed development measurements:

- FLUX resident VRAM: ~11.9 GiB
- Z-Image resident VRAM: ~7.9 GiB
- Combined resident VRAM: ~19.9 GiB
- FLUX 1024×1024 generation: ~18.8 s
- Z-Image 512×512 generation: ~25.9 s

These measurements are infrastructure validation results, **not a replacement for the official 25-prompt benchmark**.

---

## 12. Important Remaining Engineering Validation

### Concurrent GPU benchmark

Current deployment proves coexistence, but not production behavior under simultaneous requests.

Measure at least:

1. FLUX alone
2. Z-Image alone
3. FLUX + Z-Image simultaneously

Capture:

- success/failure rate
- P50 latency
- P95 latency
- throughput
- peak VRAM
- GPU utilization
- queueing behavior

This determines whether time-slicing is appropriate for the target workload.

### Resource sizing

CPU and RAM `requests` / `limits` should be added after observing actual resource usage.

Do not guess the values.

### NetworkPolicy negative test

The allowed paths have been verified.

A future security validation should also create a temporary unauthorized pod and confirm that model access is denied.

---

## 13. Components Not Added Intentionally

The following are not currently justified by the workload and hardware:

- HPA
- GPU autoscaling
- Helm
- Argo CD
- service mesh
- multi-node control plane
- scale-to-zero

They should only be added if requirements, workload, reliability targets, or available GPU capacity justify them.

---

## 14. Operational Safety Notes

- Do not delete `/data/hf-cache`.
- Do not manually remove k3s/containerd storage directories.
- Check `/data` usage before large image pulls/imports.
- Docker and k3s/containerd use separate image stores.
- A Docker image is not automatically visible to k3s.
- Keep the Docker Compose deployment as Plan A.
- Keep the k3s-specific Gradio image tagged separately as `:k3s`.
- Never commit PATs, API tokens, or passwords.

For incident history and lessons learned, see:

```text
deployment/k3s/DEPLOYMENT-TROUBLESHOOTING-REPORT.md
```
