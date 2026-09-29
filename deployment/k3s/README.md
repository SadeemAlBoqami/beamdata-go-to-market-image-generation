# ☸️ BeamData Image Generation — k3s Deployment

This directory contains the validated **k3s / Kubernetes deployment** for the BeamData Image Generation project.

The deployment runs the two final selected open-source image-generation models as independent inference services, connects them to a Gradio frontend, exposes the application through Traefik, and includes GPU sharing, monitoring, and network controls.

---

## 🏗️ Final Architecture

```text
External User
     |
     v
Traefik :80
     |
     v
Gradio :7860
   /       \
  v         v
FLUX       Z-Image
:8000       :8000
  \         /
   \       /
 NVIDIA RTX A6000
      |
 NVIDIA time-slicing
  2 logical GPU slots

Monitoring
├── Prometheus :9090
└── Grafana    :3000
```

### Service ports

| Component              |     Port |
| ---------------------- | -------: |
| Traefik external entry |   **80** |
| Gradio frontend        | **7860** |
| FLUX API               | **8000** |
| Z-Image API            | **8000** |
| Grafana                | **3000** |
| Prometheus             | **9090** |

Both model APIs listen on port `8000` inside the cluster.

---

## ✅ Deployed Workloads

Namespace:

```text
beamdata
```

contains:

- `flux2-klein`
- `z-image-turbo`
- `gradio`

Namespace:

```text
monitoring
```

contains:

- `prometheus`
- `grafana`

---

## 📁 Directory Layout

```text
deployment/k3s/
├── app/
│   ├── app.py
│   ├── Dockerfile
│   ├── README.md
│   ├── assets/
│   ├── components/
│   └── services/
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
│   ├── grafana-ingress.yaml
│   ├── grafana-service.yaml
│   ├── namespace.yaml
│   ├── prometheus-configmap.yaml
│   ├── prometheus-deployment.yaml
│   └── prometheus-service.yaml
├── network-policy/
│   └── model-network-policy.yaml
├── README.md
└── verify.sh
```

---

## 🧩 What k3s Adds

Compared with the simpler Docker Compose path, k3s provides:

- Kubernetes Deployments and desired-state reconciliation
- internal service discovery and DNS
- Namespaces
- Kubernetes Secret references
- GPU resource scheduling
- NVIDIA GPU time-slicing
- controlled rollout behavior
- Traefik ingress
- NetworkPolicy
- Prometheus and Grafana as cluster workloads
- a clearer path toward future multi-node deployment

k3s does **not** automatically provide:

- more physical GPU capacity,
- VRAM isolation,
- lower inference latency,
- public Internet access,
- or high availability on a single-node cluster.

---

## 🔐 Required Secrets

Secret values are never stored in Git.

Expected Kubernetes Secrets include:

### Model API tokens

Namespace:

```text
beamdata
```

Secret:

```text
model-tokens
```

Keys:

```text
flux-token
zimage-token
```

### Container registry pull secret

```text
ghcr-pull
```

### Grafana credentials

Namespace:

```text
monitoring
```

Secret:

```text
grafana-admin
```

Keys:

```text
admin-user
admin-password
```

Verify names only:

```bash
kubectl get secrets -n beamdata
kubectl get secrets -n monitoring
```

---

## 🚀 Recommended Deployment Order

### 1. Create namespaces

```bash
kubectl apply -f deployment/k3s/models/namespace.yaml
kubectl apply -f deployment/k3s/monitoring/namespace.yaml
```

### 2. Configure GPU time-slicing

```bash
kubectl apply -f deployment/k3s/gpu-sharing/nvidia-time-slicing-configmap.yaml
```

The NVIDIA Device Plugin patch is a patch file, not a standalone Kubernetes resource.

Follow:

```text
deployment/k3s/gpu-sharing/README.md
```

Verify logical GPU capacity after the plugin configuration is active:

```bash
kubectl get nodes
kubectl describe node
```

Expected schedulable GPU capacity:

```text
2 logical GPU slots
```

> These are scheduler-level replicas of one physical GPU, not two isolated GPUs.

### 3. Deploy model services

```bash
kubectl apply -f deployment/k3s/models/flux-service.yaml
kubectl apply -f deployment/k3s/models/flux-deployment.yaml

kubectl apply -f deployment/k3s/models/zimage-service.yaml
kubectl apply -f deployment/k3s/models/zimage-deployment.yaml
```

### 4. Build the k3s Gradio image

The k3s deployment keeps its own application variant under:

```text
deployment/k3s/app/
```

Build using that directory as the context:

```bash
docker build   -t beamdata-model-lab-gradio:k3s   -f deployment/k3s/app/Dockerfile   deployment/k3s/app
```

Import the image into k3s/containerd when required:

```bash
docker save beamdata-model-lab-gradio:k3s | sudo k3s ctr -n k8s.io images import -
```

Deploy Gradio:

```bash
kubectl apply -f deployment/k3s/frontend/gradio-service.yaml
kubectl apply -f deployment/k3s/frontend/gradio-deployment.yaml
```

### 5. Deploy monitoring

```bash
kubectl apply -f deployment/k3s/monitoring/
```

### 6. Apply ingress

```bash
kubectl apply -f deployment/k3s/ingress/gradio-ingress.yaml
```

Traefik provides the external entry point on port:

```text
80
```

### 7. Apply NetworkPolicy

Apply only after required connectivity has been verified:

```bash
kubectl apply -f deployment/k3s/network-policy/model-network-policy.yaml
```

---

## 🎨 Gradio Routing

The Gradio application itself listens on:

```text
7860
```

External access is routed through:

```text
Traefik :80
```

The AIDC environment may add an additional proxy prefix before traffic reaches Traefik.

That environment-specific prefix is supplied through:

```text
GRADIO_ROOT_PATH
```

The README intentionally does not hard-code the proxy prefix because it is environment-specific.

---

## 🧠 GPU Time-Slicing

The deployment uses the NVIDIA Device Plugin to expose:

```text
2 logical GPU slots
```

on one RTX A6000.

This allows Kubernetes to schedule:

- one FLUX Pod,
- and one Z-Image Pod

at the same time.

Important:

> NVIDIA time-slicing is scheduler sharing, not VRAM isolation.

Both model workloads still share the physical GPU's VRAM and compute capacity.

---

## 🔄 GPU-Aware Rollout Strategy

The model Deployments use:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 0
    maxUnavailable: 1
```

Why:

The cluster exposes only two logical GPU slots. A default rolling update may try to create an additional GPU-consuming Pod before terminating the old one.

That extra Pod can remain `Pending`.

`maxSurge: 0` prevents this behavior.

Trade-off:

- safer rollout on constrained GPU capacity,
- but a brief model-service interruption during updates is possible.

This trade-off is acceptable for the current capstone deployment.

---

## 🐳 Docker vs. k3s Image Stores

Docker and k3s/containerd maintain separate image stores.

A locally built Docker image is **not automatically available** to k3s.

When a locally built image is required by k3s:

```bash
docker save <image-name> | sudo k3s ctr -n k8s.io images import -
```

This was required during deployment validation.

---

## 📈 Monitoring

The cluster includes:

### Prometheus

Port:

```text
9090
```

Used for metrics collection.

### Grafana

Port:

```text
3000
```

Used for monitoring dashboards.

The validated deployment confirmed:

- both workloads running,
- Prometheus targets UP,
- and Grafana available inside the monitoring stack.

---

## 🌐 Ingress and External Access

Traefik provides the Kubernetes ingress layer and listens externally on:

```text
80
```

Ingress routing is part of the deployment architecture, but Kubernetes ingress alone does not guarantee a public Internet endpoint.

Public reachability depends on the surrounding infrastructure and AIDC access configuration.

---

## ✅ Verification

Run:

```bash
bash deployment/k3s/verify.sh
```

The verification workflow checks:

- cluster access,
- `beamdata` workloads,
- monitoring workloads,
- Services,
- Ingress,
- GPU capacity,
- current GPU processes and VRAM,
- model health from the Gradio Pod,
- Traefik routing,
- NetworkPolicy resources,
- disk usage,
- and Kubernetes manifest validation.

---

## ✅ Validated State

The final deployment validated:

- FLUX and Z-Image can coexist on one RTX A6000.
- FLUX health endpoint returns HTTP 200.
- Z-Image health endpoint returns HTTP 200.
- Gradio can reach both model Services.
- FLUX generation succeeds through the Gradio service layer.
- Z-Image generation succeeds through the Gradio service layer.
- Prometheus and Grafana are running.
- Prometheus targets were verified UP.
- Traefik routing works.
- NetworkPolicy did not break required communication paths.

Observed infrastructure validation measurements are separate from the official 25-prompt benchmark and should not replace the benchmark results.

---

## ⚠️ Operational Notes

- Do not delete active model caches.
- Check disk usage before large model pulls or image imports.
- Docker and k3s/containerd use separate image stores.
- Do not manually delete k3s/containerd storage directories.
- Never commit API tokens, PATs, or passwords.
- Keep production-style resource requests and limits evidence-based rather than guessed.

---

## 🔭 Remaining Production-Readiness Work

The capstone deployment is complete, but production hardening can continue with:

- concurrent FLUX + Z-Image benchmark,
- P50 / P95 latency measurement,
- throughput testing,
- queueing analysis,
- CPU and RAM resource sizing,
- negative NetworkPolicy testing,
- broader observability,
- and multi-node testing if future infrastructure supports it.
