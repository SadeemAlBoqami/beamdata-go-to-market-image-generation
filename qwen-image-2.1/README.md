# Qwen-Image-2.1 Feasibility and Benchmark Experiment

## Model

Qwen/Qwen-Image-2.1

## Purpose

Evaluate Qwen-Image-2.1 as an additional open-source image-generation candidate for the Beamdata Image Generation Model Evaluation and Brand Adaptation project.

The experiment focuses on:

- Model loading feasibility
- 512x512 generation
- 1024x1024 generation
- Generation latency
- Peak GPU VRAM
- Prompt success rate
- Image quality comparison against existing open-source baselines
- vLLM / vLLM-Omni serving compatibility

## Hardware

- NVIDIA RTX A6000
- 48 GB VRAM

## Runtime Used for Successful Benchmark

Qwen-Image-2.1 was successfully benchmarked using:

- Hugging Face Diffusers
- QwenImage21Pipeline
- BF16
- CPU offload
- 40 inference steps

The current tested vLLM-Omni nightly build does not register
QwenImage21Pipeline in its diffusion model registry.

Therefore, the successful benchmark results in this directory are
Diffusers-based feasibility results and not vLLM-Omni serving results.

The file:

`deployment-vllm-experimental.yaml`

documents the attempted vLLM-Omni deployment configuration and should not
be interpreted as a working production deployment.

## 512x512 Feasibility Test

People & Lifestyle category:

- Prompts tested: 5
- Success: 5/5
- Average latency including first warm-up: 54.509 s
- Average latency excluding first generation: 41.440 s
- Peak GPU VRAM: 17,345 MiB (16.94 GiB)

Results:

`results/512/`

## 1024x1024 Full Benchmark

All 25 official benchmark prompts were successfully generated.

Results:

- Success rate: 25/25
- Average latency: 77.465 s
- Median latency: 70.606 s
- Minimum latency: 62.601 s
- Maximum latency: 152.398 s
- Peak GPU VRAM: 17,355 MiB (16.95 GiB)

The 25 prompts were executed across two Kubernetes pods.

PL-01 and TT-01 contain cold-start / warm-up overhead because each was the
first generation after loading the model in a new pod.

Full benchmark CSV:

`results/1024/qwen_full_25_1024.csv`

Benchmark summary:

`results/1024/benchmark_summary.md`

## Existing Open-Source Baselines

- FLUX.2 Klein 4B
- Stable Diffusion 3.5 Medium

Qwen-Image-2.1 should be compared against these models using image quality,
prompt adherence, latency, VRAM usage, serving compatibility, and later
brand-adaptation feasibility.

## Current Technical Status

Qwen-Image-2.1 is technically feasible for image generation on the available
RTX A6000 development hardware.

At 1024x1024, peak observed GPU memory with CPU offload was approximately
16.95 GiB.

However, a working vLLM-Omni serving path has not yet been confirmed because
the tested vLLM-Omni nightly build does not currently register
QwenImage21Pipeline.

This serving compatibility limitation must be considered separately from
the successful Diffusers inference benchmark.
