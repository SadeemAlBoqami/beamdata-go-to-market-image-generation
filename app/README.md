# Image Generation Model Evaluation UI

A Gradio Blocks frontend for generating images with separately deployed FLUX
and Z-Image Turbo services, and reviewing saved final-model benchmark results.
Qwen Image is visible in the Generate layout but unavailable in the current
deployment. Model startup and orchestration are intentionally outside this app.

## Dependencies and setup

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "gradio==6.28.0" requests Pillow
```

## Backend configuration

Set endpoint URLs to the externally running `/v1/images/generations` APIs.
The backend deployment scripts require Bearer tokens, supplied separately to
the frontend. Do not store tokens in this repository.

```bash
export FLUX_ENDPOINT=http://127.0.0.1:8005/v1/images/generations
export FLUX_TOKEN='<FLUX_API_TOKEN>'
export ZIMAGE_ENDPOINT=http://127.0.0.1:8092/v1/images/generations
export ZIMAGE_TOKEN='<ZIMAGE_API_TOKEN>'
```

`FLUX_ENDPOINT` defaults to the URL above. `ZIMAGE_ENDPOINT` has no default
because the deployment container exposes port 8000 internally while host port
mapping varies; the 8092 example comes from the repository's Z-Image benchmark
runner. Use the host-mapped URL for your deployment. `FLUX_TOKEN` and
`ZIMAGE_TOKEN` are sent only as Bearer headers to their respective endpoints.

## Run

```bash
.venv/bin/python -m app.app
```

The app listens on port 7860 with `root_path=/proxy/7860` for the AIDC
reverse proxy. Open the URL printed by Gradio through that proxy.

The Generate tab offers four aspect ratios. The saved deployment validation
covers 512×512 images; other requested dimensions depend on the deployed
backend's support. Generated downloads use a process-local temporary folder
and are removed when the app exits. No permanent image storage is created.

The Benchmark Comparison tab reads existing prompt JSON and final-model CSV
and image files under `benchmark/`. It never reruns a benchmark. Model identities
can be revealed in the card details; A/B preference submissions are confirmed
in the current session only and do not modify Phase 2 evaluation data.
