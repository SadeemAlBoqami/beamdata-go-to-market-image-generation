# Qwen-Image-2.1 Feasibility Experiment

Model:
Qwen/Qwen-Image-2.1

Purpose:
Evaluate Qwen-Image-2.1 as an additional open-source image-generation candidate for the Beamdata project.

Goals:
- Confirm model loading
- Confirm serving path
- Test 512x512 generation
- Measure generation latency
- Measure peak VRAM
- Test 1024x1024 generation if feasible
- Compare image quality with FLUX.2 Klein 4B and Stable Diffusion 3.5 Medium

Hardware:
- NVIDIA RTX A6000
- 48 GB VRAM

Initial scope:
Smoke test only. Full 25-prompt benchmarking will only be performed if the model is technically promising.

Existing baselines:
- FLUX.2 Klein 4B
- Stable Diffusion 3.5 Medium
