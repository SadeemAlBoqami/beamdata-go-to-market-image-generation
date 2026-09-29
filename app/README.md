# 🎨 Image Generation Model Evaluation UI

A **Gradio** frontend for the BeamData Image Generation project.

It provides a single interface for:

- generating images with the deployed **FLUX.2 Klein** and **Z-Image-Turbo** services,
- reviewing saved benchmark results,
- comparing model outputs,
- and collecting pairwise human-evaluation feedback.

> The application itself does not load the image-generation models.
> Model inference runs in separate authenticated services.

---

## ✨ Main Features

| Feature              | Description                                                           |
| -------------------- | --------------------------------------------------------------------- |
| Generate             | Send prompts to FLUX and Z-Image inference APIs                       |
| Benchmark Comparison | Review saved commercial and open-source benchmark outputs             |
| Human Evaluation     | Compare two saved images and record A / B / Tie decisions             |
| Technical Metadata   | Display available latency, resolution, status, and benchmark metadata |

---

## 🧩 Application Architecture

```text
Gradio UI :7860
   |
   +------> FLUX API
   |
   +------> Z-Image API
```

In the final k3s deployment:

```text
External User
     |
     v
Traefik :80
     |
     v
Gradio :7860
     |
     +------> FLUX API :8000
     |
     +------> Z-Image API :8000
```

The model APIs are protected using Bearer-token authentication.

---

## ⚙️ Setup

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "gradio==6.28.0" requests Pillow
```

For environments that use the evaluation workbook features, install:

```bash
.venv/bin/python -m pip install "openpyxl==3.1.5"
```

---

## 🔐 Backend Configuration

Configure the frontend using environment variables.

Example for a local or Docker-hosted setup:

```bash
export FLUX_ENDPOINT=http://127.0.0.1:8005/v1/images/generations
export FLUX_TOKEN='<FLUX_API_TOKEN>'

export ZIMAGE_ENDPOINT=http://127.0.0.1:8006/v1/images/generations
export ZIMAGE_TOKEN='<ZIMAGE_API_TOKEN>'
```

The example ports `8005` and `8006` are host mappings and may differ by environment.

Inside the final Kubernetes deployment, both model services listen on:

```text
8000
```

Tokens must be supplied externally and must **never** be committed to the repository.

---

## ▶️ Run the App

From the repository root:

```bash
.venv/bin/python -m app.app
```

The Gradio application listens on:

```text
7860
```

In the k3s deployment, external access is routed through **Traefik on port 80**.

The proxy prefix is environment-specific and is controlled through:

```text
GRADIO_ROOT_PATH
```

This keeps the application portable between local, Docker Compose, and AIDC/k3s environments.

---

## 🖼️ Generation

The final deployed models are:

- **FLUX.2 Klein 4B Q4_K_M**
- **Z-Image-Turbo W4**

The final project benchmark for both selected open-source models was performed at **512×512**.

The interface also supports additional validated aspect ratios where configured by the active deployment.

---

## 📊 Benchmark Comparison

The Benchmark Comparison tab reads the official saved benchmark artifacts under:

```text
benchmark/
```

It displays existing results only. It does **not** rerun inference.

The stored benchmark data includes:

- prompt and category,
- model,
- resolution,
- generation time,
- success / failure status,
- image reference,
- and available runtime metadata.

> Commercial benchmark images were generated at 1024×1024, while the final selected open-source models were benchmarked at 512×512. Cross-group latency values should therefore be interpreted within their benchmark context.

---

## 👥 Human Evaluation

The Human Evaluation tab supports pairwise comparison of saved images.

The evaluator can submit:

```text
A / B / Tie
```

Optional detailed scoring may also be recorded where enabled.

New pairwise evaluations are written to:

```text
evaluation/data/pairwise_human_evaluation.csv
```

This does not overwrite the earlier commercial evaluation files or the final five-model ranking dataset.

---

## 📁 Source Layout

```text
app/
├── app.py
├── Dockerfile
├── README.md
├── assets/
├── components/
└── services/
```

### Main responsibilities

```text
components/
├── generation.py          # image generation UI
├── benchmark.py           # benchmark comparison
├── evaluation.py          # evaluation views
└── human_evaluation.py    # pairwise human evaluation

services/
├── flux_service.py
├── zimage_service.py
├── health_service.py
└── ...
```

---

## ☸️ k3s-Specific Variant

The repository intentionally keeps a second application variant under:

```text
deployment/k3s/app/
```

That copy contains deployment-specific behavior for the validated k3s environment, including:

- AIDC proxy handling,
- k3s container dependencies,
- deployment-specific download behavior,
- and validated 512×512 FLUX defaults.

`app/` remains the main application source, while `deployment/k3s/app/` represents the deployment-specific k3s variant.

---

## ✅ Final Status

The frontend was validated against both selected model services in the k3s deployment.

Confirmed:

- Gradio can reach both model services.
- FLUX image generation succeeds through the frontend service layer.
- Z-Image generation succeeds through the frontend service layer.
- Bearer-token protected inference is supported.
- Benchmark and human-evaluation artifacts are accessible through the UI workflow.
