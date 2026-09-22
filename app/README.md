# Image Generation Model Evaluation UI

This is a Gradio Blocks frontend for comparing image-generation models for
marketing use cases. It does not load models or use GPUs in the Gradio process;
selected FLUX requests are sent to the already-running local vLLM-Omni endpoint.
It does not run benchmarks or save human-evaluation results.

## Setup

From the repository root, create and activate a virtual environment if needed,
then install the single frontend dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install "gradio==6.28.0" requests Pillow
```

## Run

From the repository root:

```bash
.venv/bin/python -m app.app
```

Open the local URL printed by Gradio (normally `http://127.0.0.1:7860`).

## Future integration points

- `services/flux_service.py` calls the local FLUX vLLM-Omni endpoint. Z-Image
  Turbo and Qwen Image service functions remain intentionally unimplemented.
- `load_benchmark_results_placeholder()` in `app.py` is the boundary for
  reading existing benchmark CSV/JSON results later. It must not rerun a
  benchmark.
- The evaluation submit action validates UI input only; it does not write to
  any project dataset.
