Phase 3 - Open-Source Model Feasibility Evaluation

1. Test Environment

Test Environment

GPU: NVIDIA RTX A6000

VRAM: 48 GB

Driver: 550.90.12

CUDA: 12.4

OS: Ubuntu 22.04

Kubernetes: k3s v1.36.4

Container Runtime: containerd

GPU Count: 1

2. Original Feasibility Template

FLUX.2 Klein 4B

Model:

black-forest-labs/FLUX.2-klein-4B

Serving:

vLLM-Omni

Feasibility Results

Model load:

TBD

512x512 generation:

TBD

Peak VRAM:

TBD

Generation latency:

TBD

Reliability:

TBD

vLLM / vLLM-Omni compatibility:

TBD

Deployment complexity:

TBD

Runtime optimizations:

TBD

Errors / observations:

TBD

Stable Diffusion 3.5 Medium

Model:

stabilityai/stable-diffusion-3.5-medium

Serving:

vLLM-Omni

Feasibility Results

Model load:

TBD

512x512 generation:

TBD

Peak VRAM:

TBD

Generation latency:

TBD

Reliability:

TBD

vLLM / vLLM-Omni compatibility:

TBD

Deployment complexity:

TBD

Runtime optimizations:

TBD

Errors / observations:

TBD

3. Completed Feasibility Results

FLUX.2 Klein 4B

Model:

black-forest-labs/FLUX.2-klein-4B

Serving:

vLLM-Omni

Feasibility Results

Model load:

PASS

512x512 generation:

PASS

Peak VRAM:

TBD

Generation latency:

5.141 s (single successful 512x512 smoke test via port-forward)

Reliability:

TBD

vLLM / vLLM-Omni compatibility:

PASS

Deployment complexity:

Moderate

Runtime optimizations:

Used updated runtime/image after initial CUDA runtime mismatch.

Errors / observations:

Initial attempt failed with libcudart.so.13 mismatch.

After updating the runtime/container, the model loaded successfully and generated a valid 512x512 PNG image.

FLUX.2 Klein 4B - Attempt 1

Container start: FAIL

Failure stage: vLLM initialization

Error:

libcudart.so.13 not found

Root cause:

The prebuilt vLLM 0.28.0 wheel targets CUDA 13, while the target server exposes a CUDA 12.4 environment.

VRAM/OOM:

Not reached. Model loading did not begin.

Next action:

Use a CUDA-compatible vLLM build/runtime and retry.

Reliability:

PASS — 5/5 successful 512x512 generations.

Latency:

Average: 5.145 s

Min: 5.115 s

Max: 5.190 s

Test setup:

Prompt: PL-01

Resolution: 512x512

Seed: 42

GPU: NVIDIA RTX A6000 48 GB

Serving runtime: vLLM-Omni

FLUX.2 Klein 4B successfully serves and generates 512×512 images on the RTX A6000 48 GB development GPU, with 5/5 reliability and ~5.15 s average latency. Compatibility with the ~16 GB production VRAM target is not yet demonstrated and requires accurate peak-VRAM measurement and potentially runtime optimization.

Stable Diffusion 3.5 Medium

Model:

stabilityai/stable-diffusion-3.5-medium

Serving:

vLLM-Omni

Model load:

PASS

512x512 generation:

PASS

Reliability:

PASS — 5/5 successful generations

Latency:

Average: 1.244 s

Min: 1.225 s

Max: 1.271 s

Peak VRAM:

32,380 MiB (~31.62 GiB)

GPU:

NVIDIA RTX A6000 48 GB

16 GB production target:

FAIL in current configuration

Observations:

SD 3.5 Medium is significantly faster than FLUX.2 Klein 4B at 512x512 in the current setup, but uses substantially more VRAM.

Further optimization or quantization would be required to make it viable for a ~16 GB deployment target.

4. Initial Model Comparison Notes

FLUX.2 Klein 4B

Latency: ~5.15 s

Peak VRAM: ~16.07 GiB

Reliability: 5/5

16 GB target: borderline

SD 3.5 Medium

Latency: ~1.24 s

Peak VRAM: ~31.62 GiB

Reliability: 5/5

16 GB target: fail

Increasing SD 3.5 Medium from 512×512 to 1024×1024 produced a visible improvement in image detail and marketing-quality presentation, but increased latency from ~1.24 s to 4.06 s and peak VRAM from ~31.6 GiB to ~35.0 GiB.

At 1024×1024, both recommended open models exceeded the project’s approximate 16 GB VRAM target.

FLUX.2 Klein 4B used slightly less VRAM than SD 3.5 Medium, but was significantly slower.

SD 3.5 Medium was substantially faster, but still far above the intended 16 GB deployment target.

Troubleshooting and Benchmark Procedure Notes

Port-forward identification

When multiple kubectl port-forward processes were active, ps and /proc/<pid>/cmdline
did not expose the original arguments because the process title had been shortened to kubectl.

The practical method used to identify the correct FLUX endpoint was to query the available local ports:

curl -s http://localhost:8000/v1/models
curl -s http://localhost:8002/v1/models

The port returning:

black-forest-labs/FLUX.2-klein-4B

was selected as the FLUX endpoint.

Example:

export FLUX_KLEIN_BASE_URL=http://localhost:8000

or:

export FLUX_KLEIN_BASE_URL=http://localhost:8002

1024×1024 FLUX benchmark

The benchmark was executed using the FLUX endpoint and prompt PL-01.

VRAM was monitored continuously using:

while true; do
  echo -n "$(date +%H:%M:%S.%3N),"
  nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits
  sleep 0.2
done | tee /tmp/flux_1024_vram.csv

Peak observed VRAM was extracted using:

cut -d',' -f2 /tmp/flux_1024_vram.csv | sort -n | tail -1

Observed FLUX result:

Model: black-forest-labs/FLUX.2-klein-4B

Endpoint: http://localhost:8002

Resolution: 1024×1024

Success: PASS

Generation latency: 16.653 s

Peak VRAM: 34,902 MiB

6. Final 1024×1024 Comparison and Decision Options

Excellent — this gives the first fair 1024×1024 comparison.

Observed result

FLUX.2 Klein 4B @ 1024×1024

Success: PASS

Latency: 16.653 s

Peak VRAM: 34902 MiB ≈ 34.08 GiB

Comparison with SD 3.5 Medium @ 1024×1024

SD 3.5 Medium @ 1024×1024

Success: PASS

Latency: 4.064 s

Peak VRAM: 35850 MiB ≈ 35.01 GiB

Key engineering conclusion

Latency:

SD 3.5 is significantly faster.

Approximately:

SD 3.5 = 4.06s

FLUX = 16.65s

FLUX is approximately 4.1× slower at the same resolution.

VRAM:

The difference between them is small at 1024×1024.

FLUX = 34.08 GiB

SD 3.5 = 35.01 GiB

FLUX uses approximately:

948 MiB ≈ 0.93 GiB

This is a small difference and does not materially change the overall conclusion.

Most important conclusion for the 16 GB target

Both models fail to meet the ~16 GB VRAM target at 1024×1024.

This is the most important Phase 3 finding so far.

Specifically:

FLUX at 512×512 was borderline and close to the target.

At 1024×1024, it increased to ~34 GiB.

SD 3.5 was already above 16 GB at 512×512 and reached ~35 GiB at 1024×1024.

What this means for the project

This provides a clear finding for the report:

At 1024×1024, both recommended open models exceeded the project’s approximate 16 GB VRAM target.

FLUX.2 Klein 4B used slightly less VRAM than SD 3.5 Medium, but was significantly slower.

SD 3.5 Medium was substantially faster, but still far above the intended 16 GB deployment target.

This is not a failure.

It is a valuable benchmark finding.

Key comparison summary so far

FLUX.2 Klein 4B

512×512

Latency: ~5.15 s

Peak VRAM: 16459 MiB ≈ 16.07 GiB

Reliability: 5/5

1024×1024

Latency: 16.653 s

Peak VRAM: 34902 MiB ≈ 34.08 GiB

Reliability: PASS

SD 3.5 Medium

512×512

Latency: ~1.24 s

Peak VRAM: 32380 MiB ≈ 31.62 GiB

Reliability: 5/5

1024×1024

Latency: 4.064 s

Peak VRAM: 35850 MiB ≈ 35.01 GiB

Reliability: PASS

FLUX scales badly in VRAM when moving from 512 to 1024.

Option A — You complete the full benchmark on the models as they are

Because they are the officially required ones

Then in the report, you clearly state that they don’t achieve 16GB at 1024

Option B — You consider FLUX as the closest to the 16GB target

And use it as the main deployment candidate, especially if the final benchmark is on 512 or if they accept a trade-off

Option C — You add a third, lighter candidate

If you want an open-source model that gets closer to the 16GB requirement at 1024

But this is an extra decision, not necessary right away

7. Report-Ready Summary

Feasibility testing showed that both recommended open models could be served successfully on the available RTX A6000 (48 GB), but neither satisfied the approximate 16 GB VRAM target at 1024×1024 resolution. FLUX.2 Klein 4B reached ~34.1 GiB and required 16.65 seconds per image, while SD 3.5 Medium reached ~35.0 GiB and required 4.06 seconds per image. At 512×512, FLUX was much closer to the 16 GB target (~16.1 GiB), whereas SD 3.5 Medium still required ~31.6 GiB.

Update:

I completed the full official benchmark for FLUX.2 Klein 4B on all 25 prompts at 512×512.

All 25/25 generations succeeded.

Latency was consistent at about 5.1–5.3 seconds per image.

Recorded peak VRAM was 34902 MiB.

Results are saved in:

benchmark/results/open_source_benchmark_results.csv

| Metric       |                 FLUX.2 Klein 4B | SD 3.5 Medium |

| ------------ | ------------------------------: | ------------: |

| Success rate |                            100% |          100% |

| Avg latency  |                          ~5.2 s |   1.236 s |

| Peak VRAM    | ~34.9 GiB recorded in this run* | 31.62 GiB |

| Resolution   |                         512×512 |       512×512 |

Phase 3 update:

I completed the full 25-prompt benchmark at 512×512 for both deployed models.

FLUX.2 Klein 4B: 25/25 successful, 5.20s average latency.

SD 3.5 Medium: 25/25 successful, 1.236s average latency, ~31.62 GiB recorded peak VRAM.

SD3.5 is significantly faster, but its current configuration is well above the ~16 GB target.

Can someone take SDXL Base 1.0 as the third candidate feasibility test @512×512 so we can compare all three candidates before confirming the final two?

The current tested configurations do not meet the ~16 GB deployment target. Further candidate testing and/or memory optimization is required.