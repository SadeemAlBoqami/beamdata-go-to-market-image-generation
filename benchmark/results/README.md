# Model Evaluation Results

This directory contains the complete model evaluation history for the image generation project.

## Purpose

The `phase3-all-model-evaluations` branch preserves all evaluated models, benchmark runs, images, runtime variants, unsuccessful attempts, and raw benchmark artifacts.

Only selected final deployment models will later be promoted to `main`.

## Commercial Benchmarks

All commercial models were evaluated using the same 25 benchmark prompts at 1024x1024.

- OpenAI GPT Image 2 — 25/25
- BFL FLUX 2 Pro — 25/25
- Google Gemini 3.1 Flash Image — 25/25

Location:

`benchmark/results/commercial/`

## Open-Source Evaluations

### FLUX.2 Klein 4B

Evaluated in multiple configurations:

- Baseline @512
- Baseline @1024
- GGUF Q4_K_M @512

Q4_K_M result:

- Success: 25/25
- Average latency: 6.705 s
- Peak VRAM: 11.67 GiB
- Runtime: vLLM-Omni

Location:

`benchmark/results/open_source/flux2-klein/`

### Z-Image-Turbo

Evaluated as:

- Baseline @512
- BitsAndBytes W4 @512
- Earlier partial attempts retained for traceability

W4 result:

- Success: 25/25
- Average latency: 14.554 s
- Peak VRAM: 7.86 GiB
- Runtime: vLLM-Omni

Location:

`benchmark/results/open_source/z-image-turbo/`

### Qwen-Image-2.1

vLLM-Omni @512:

- Success: 25/25
- Average latency: ~7.77 s
- Peak VRAM: ~34.03 GiB

Serving was successful, but VRAM consumption was significantly above the project's approximately 16 GB deployment target.

Location:

`benchmark/results/open_source/qwen-image-2.1/`

### Stable Diffusion 3.5 Medium

Successfully benchmarked at 512 and 1024.

Not selected for final deployment because the tested configuration did not provide competitive visual quality and prompt adherence.

Location:

`benchmark/results/open_source/sd35-medium/`

### SDXL Base 1.0

Successfully benchmarked at 512.

Not selected for final deployment because visual quality and prompt adherence in the tested configuration were not acceptable for the project.

Location:

`benchmark/results/open_source/sdxl-base/`

## Current Final Candidates

The current deployment candidates are:

- FLUX.2 Klein 4B — GGUF Q4_K_M
- Z-Image-Turbo — W4

Both completed all 25 required 512x512 benchmark prompts using vLLM-Omni while remaining below approximately 16 GB peak VRAM.

Final selection also considers visual quality and prompt adherence.

## Master Index

A consolidated index of benchmark runs is available at:

`benchmark/results/model_run_index.csv`

## Legacy Data

Original/raw result files are retained under:

`benchmark/results/_legacy_raw/`

They are preserved for traceability and should not be used as the primary organized results source.
