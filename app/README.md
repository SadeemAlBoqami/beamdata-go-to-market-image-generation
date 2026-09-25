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
export ZIMAGE_ENDPOINT=http://127.0.0.1:8006/v1/images/generations
export ZIMAGE_TOKEN='<ZIMAGE_API_TOKEN>'
```

`FLUX_ENDPOINT` defaults to the URL above. `ZIMAGE_ENDPOINT` has no default
because the deployment container exposes port 8000 internally while host port
mapping varies. The 8006 example matches the current AIDC deployment; use the
host-mapped URL for your deployment. `FLUX_TOKEN` and
`ZIMAGE_TOKEN` are sent only as Bearer headers to their respective endpoints.

## Run

```bash
.venv/bin/python -m app.app
```

The app listens on port 7860 with `root_path=/proxy/7860` for the AIDC
reverse proxy. Open the URL printed by Gradio through that proxy.

The Generate tab offers four validated aspect ratios: FLUX uses 1024×1024,
768×1024, 576×1024, and 1024×768; Z-Image uses 512×512, 384×512,
288×512, and 512×384. Generated downloads use a process-local temporary
folder and are removed when the app exits. No permanent image storage is created.

The Benchmark Comparison tab reads existing prompt JSON and official saved
CSV/image outputs under `benchmark/`. It shows one result per model and available
technical metadata. These saved runs use 1024×1024 commercial images and
512×512 open-source images, so metrics are descriptive rather than a controlled
same-resolution comparison. It never runs inference or collects votes. Duplicate
eligible official rows are flagged as ambiguous instead of guessed.

The Human Evaluation tab compares two named saved images at a time. Enter an
Evaluator ID, choose A/B/Tie, and use Save Evaluation or Save & Next. The
collapsed Detailed scoring section is optional. Votes and optional ratings are
appended to `evaluation/data/pairwise_human_evaluation.csv`; existing Phase 2
and legacy five-model evaluation files are not changed. Docker Compose mounts
`evaluation/data` read-write so votes persist across frontend restarts.
