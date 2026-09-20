# Qwen-Image-2.1 Benchmark Summary

## Configuration
- Resolution: 1024x1024
- Prompts: 25 official benchmark prompts
- Inference steps: 40
- Runtime: Diffusers
- Memory strategy: CPU offload
- Model: Qwen-Image-2.1

## Results
- Success rate: 25/25
- Average latency: 77.465 s
- Median latency: 70.606 s
- Minimum latency: 62.601 s
- Maximum latency: 152.398 s
- Peak GPU VRAM: 17,355 MiB (16.95 GiB)

## Notes
- The 25 prompts were executed across two Kubernetes pods.
- PL-01 and TT-01 include cold-start / warm-up overhead because each was the first generation in a new pod.
- Qwen-Image-2.1 currently runs successfully through Diffusers with CPU offload.
- The currently tested vLLM-Omni nightly build does not register QwenImage21Pipeline, so this benchmark is not a vLLM-Omni serving benchmark.
- Peak VRAM remained close to 17 GiB at 1024x1024 under CPU offload.
