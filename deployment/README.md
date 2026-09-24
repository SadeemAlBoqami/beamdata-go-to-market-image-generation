# Final Open-Source Models — Deployment & Benchmark

This phase validates the final open-source models selected for full deployment and benchmarking.

## Selected Models

### FLUX.2 Klein 4B Q4_K_M
- Runtime: vLLM-Omni
- Resolution: 512×512
- Benchmark: 25/25 successful
- Peak VRAM: ~11.7 GiB
- Avg. generation time: ~6.7 s/image
- Deployment: Dockerized
- API authentication: Verified

### Z-Image-Turbo W4
- Runtime: vLLM-Omni
- Resolution: 512×512
- Benchmark: 25/25 successful
- Peak VRAM: ~7.9 GiB
- Avg. generation time: ~14.6 s/image
- Deployment: Dockerized
- API authentication: Verified

## Validation

Both selected models were:
- Served through vLLM / vLLM-Omni
- Tested using the same 25 benchmark prompts at 512×512
- Exposed through HTTP API endpoints
- Protected using Bearer-token authentication
- Evaluated for latency, VRAM usage, reliability, and image quality

## Result

Both models satisfy the core deployment and benchmarking requirements and will be used for the final commercial-vs-open-source comparison and side-by-side human evaluation.
