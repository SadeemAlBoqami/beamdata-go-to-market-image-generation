# 🚀 Final Model Deployment

This directory contains the deployment assets for the two final open-source image-generation models selected in the BeamData capstone project:

- **FLUX.2 Klein 4B Q4_K_M**
- **Z-Image-Turbo W4**

Both models were benchmarked successfully at **512×512**, served through **vLLM / vLLM-Omni**, containerized, exposed through authenticated HTTP APIs, and deployed on **k3s / Kubernetes**.

---

## ✅ Final Deployment Summary

| Component                | Final State           |
| ------------------------ | --------------------- |
| FLUX.2 Klein             | Deployed              |
| Z-Image-Turbo            | Deployed              |
| vLLM / vLLM-Omni serving | Validated             |
| Docker images            | Built and tested      |
| Bearer authentication    | Verified              |
| Gradio frontend          | Deployed              |
| k3s / Kubernetes         | Validated             |
| NVIDIA GPU time-slicing  | Configured            |
| Traefik ingress          | Validated             |
| Prometheus               | Running               |
| Grafana                  | Running               |
| NetworkPolicy            | Applied and validated |

---

## 📊 Selected Model Results

| Model                  | Benchmark | Avg. Generation Time | Peak VRAM |
| ---------------------- | --------: | -------------------: | --------: |
| FLUX.2 Klein 4B Q4_K_M |     25/25 |               ~6.7 s | ~11.7 GiB |
| Z-Image-Turbo W4       |     25/25 |              ~14.6 s |  ~7.9 GiB |

These are the official final 512×512 benchmark results used for model selection and comparison.

---

## 🏗️ Deployment Architecture

```text
External User
     |
     v
Traefik :80
     |
     v
Gradio :7860
     |
     +--------> FLUX API :8000
     |
     +--------> Z-Image API :8000

Monitoring
├── Grafana    :3000
└── Prometheus :9090

GPU
└── NVIDIA RTX A6000
    └── NVIDIA time-slicing
        ├── logical GPU slot 1
        └── logical GPU slot 2
```

### Official service ports

| Service                  |     Port |
| ------------------------ | -------: |
| Traefik / external entry |   **80** |
| Gradio frontend          | **7860** |
| FLUX inference API       | **8000** |
| Z-Image inference API    | **8000** |
| Grafana                  | **3000** |
| Prometheus               | **9090** |

Both model APIs use port `8000` **inside the Kubernetes cluster**.

---

## 📁 Directory Structure

```text
deployment/
├── README.md
├── VALIDATION.md
├── runtime-versions.txt
├── compose/
│   ├── README.md
│   ├── prometheus.yml
│   └── grafana/
├── flux2-klein/
│   ├── Dockerfile
│   └── serve/
├── z-image-turbo/
│   ├── Dockerfile
│   └── serve/
└── k3s/
    ├── app/
    ├── frontend/
    ├── gpu-sharing/
    ├── ingress/
    ├── models/
    ├── monitoring/
    ├── network-policy/
    ├── README.md
    └── verify.sh
```

---

## 🐳 Deployment Paths

Two deployment paths are maintained.

### Docker / Docker Compose

Used as the simpler single-node deployment path and local integration baseline.

See:

```text
deployment/compose/
```

### k3s / Kubernetes

Used to validate more production-oriented infrastructure behavior:

- service discovery,
- Kubernetes Secrets,
- GPU-aware scheduling,
- GPU time-slicing,
- rollout control,
- ingress,
- monitoring,
- and network policy.

See:

```text
deployment/k3s/
```

---

## 🔐 API Authentication

Both model APIs support Bearer-token authentication.

Example request header:

```http
Authorization: Bearer <TOKEN>
```

Secrets and tokens are injected at runtime and must never be committed to Git.

---

## 🧠 GPU Sharing

The deployment runs both selected models on one NVIDIA RTX A6000.

The NVIDIA Device Plugin is configured with **two logical GPU replicas** through time-slicing.

Important:

> Time-slicing enables Kubernetes scheduler sharing. It does not provide VRAM isolation.

Both models still share the same physical GPU memory and compute resources.

---

## 📈 Monitoring

The Kubernetes deployment includes:

- **Prometheus** for metric collection
- **Grafana** for dashboards and visualization

Validated infrastructure state includes:

- Prometheus running,
- Grafana running,
- Prometheus targets reported UP.

---

## 🛠️ Infrastructure Problems Solved

The deployment work addressed several real infrastructure issues:

### GPU scheduling

A single physical GPU originally exposed only one schedulable GPU resource. NVIDIA time-slicing was configured to expose two logical slots.

### Disk pressure

Large model files, caches, Docker images, and containerd snapshots caused storage pressure. Unused assets were cleaned while preserving active model files and caches.

### Docker vs. containerd

Docker and k3s/containerd use different image stores. Required images were exported from Docker and imported into k3s/containerd.

### GPU-aware rolling updates

Default Kubernetes rollout behavior could attempt to create a third GPU-consuming Pod. Model deployments therefore use:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 0
    maxUnavailable: 1
```

This prevents an additional GPU Pod from being scheduled during rollout.

---

## ✅ Validation

The deployment has validated:

- both selected models running on the same RTX A6000,
- FLUX health endpoint returning HTTP 200,
- Z-Image health endpoint returning HTTP 200,
- Gradio connectivity to both model Services,
- real image generation through both frontend service paths,
- authenticated model access,
- Traefik ingress routing,
- Prometheus and Grafana workloads,
- Prometheus targets,
- and NetworkPolicy compatibility with required traffic.

For validation details, see:

```text
deployment/VALIDATION.md
deployment/k3s/README.md
```

---

## ⚠️ Known Limits

The current deployment validates functional single-node operation.

It does not yet prove:

- production-scale concurrency,
- sustained multi-user throughput,
- multi-node high availability,
- VRAM isolation,
- or useful GPU autoscaling with only one physical GPU.

These are future production-readiness tasks rather than missing capstone requirements.

---

## ➡️ Next Step

The deployment is complete for the capstone scope.

Future work should focus on:

- concurrency and sustained-load testing,
- production resource sizing,
- expanded monitoring,
- 1024×1024 production-resolution testing,
- and integration into the wider BeamData AI Hub.
