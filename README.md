# AIDC Capstone — Image Generation Model Evaluation & Deployment

**Use Case 6: Go-to-Market Content Generation**  
**Team Progress Snapshot — 21 Sep 2026**

> **Current status:** Commercial benchmarking and evaluation are complete. Open-source feasibility testing is substantially complete. We are now validating the strongest final candidates through vLLM/vLLM-Omni and preparing the final deployment, authenticated API, side-by-side evaluation, and report.

---

## 1. Project Goal

Evaluate whether open-source image-generation models can be a practical alternative or complement to the commercial image-generation models used by the platform.

The final solution must balance:

- Image quality
- Prompt adherence
- Generation latency
- Reliability
- GPU / VRAM usage
- vLLM / vLLM-Omni compatibility
- Deployment complexity
- Licensing suitability
- API access and authentication

The target deployment environment should be designed with **approximately 16 GB VRAM** in mind.

---

## 2. Official Project Requirements — Progress

| Requirement | Status |
|---|---|
| Fixed benchmark of 25 prompts across 5 marketing categories | ✅ Complete |
| Benchmark 3 commercial models using the same prompts | ✅ Complete |
| Commercial-model evaluation | ✅ Complete |
| Evaluate initial open-source candidates | ✅ Complete |
| Investigate additional practical candidates where useful | ✅ Complete |
| Select at least 2 open-source models for final deployment | 🔄 Final validation in progress |
| Deploy final models through vLLM / vLLM-Omni | 🔄 In progress |
| Run final 512×512 benchmark: 25 prompts per selected model | 🔄 In progress |
| Record latency, peak VRAM, failures, image references, etc. | ✅ Implemented |
| Containerized inference services | 🔄 Final deployment pending |
| HTTP API for each selected model | 🔄 Prototype serving validated; final deployment pending |
| API key / Bearer authentication | ⏳ Pending |
| Side-by-side human evaluation | ⏳ Pending |
| Final technical report and presentation | 🔄 In progress |

---

## 3. Project Workflow

```mermaid
flowchart LR
    A[25 Fixed Marketing Prompts] --> B[Commercial Benchmark]
    B --> C[Commercial Evaluation]
    C --> D[Open-Source Feasibility]
    D --> E[Model Selection]
    E --> F[vLLM / vLLM-Omni Deployment]
    F --> G[Final 512 Benchmark]
    G --> H[Side-by-Side Human Evaluation]
    H --> I[Final Recommendation & Report]
```

---

# Phase 1 — Commercial Benchmark

## Goal
Establish a fixed baseline using the same 25 marketing prompts for the three commercial image-generation models.

## Models

- OpenAI GPT Image 2
- Black Forest Labs FLUX 2 Pro
- Google Gemini 3.1 Flash Image / Nano Banana 2

## Benchmark Structure

- **5 categories**
- **5 prompts per category**
- **25 prompts per model**
- **75 commercial benchmark images total**

### Categories

1. People & Lifestyle
2. Text & Typography
3. Branding & Advertising
4. Products & Physical Objects
5. Complex Compositions

### Status

**✅ COMPLETE**

The same prompt set is now reused throughout open-source evaluation so that comparisons remain consistent.

---

# Phase 2 — Commercial Evaluation

## Goal
Create the quality baseline that open-source candidates will be compared against.

### Status

**✅ COMPLETE**

Commercial outputs were generated and evaluated using the shared benchmark prompt set.

---

# Phase 3 — Open-Source Model Feasibility

## Goal
Determine which open-source models are practical candidates for final deployment.

The feasibility stage evaluates:

- Model loading
- 512×512 generation
- vLLM / vLLM-Omni compatibility
- Latency
- Peak VRAM
- Reliability
- Image quality / prompt adherence
- Runtime requirements
- Deployment complexity

---

## 4. Open-Source Models Tested

### 512×512 Results

| Model | Result | Avg Latency | Peak VRAM | vLLM / Omni | Visual Outcome | Current Decision |
|---|---:|---:|---:|---|---|---|
| **FLUX.2 Klein 4B** | 25/25 | **5.20 s** | **34.08 GiB** | ✅ | Good, but more visible errors than Z in our outputs | Candidate |
| **Stable Diffusion 3.5 Medium** | 25/25 | **1.24 s** | **31.62 GiB** | ✅ | Good and very fast | Strong fallback |
| **SDXL Base 1.0** | 25/25 | **4.44 s** | **8.22 GiB** | ✅ | Unacceptable prompt adherence / visual output in tested serving configuration | Excluded from final shortlist |
| **Z-Image-Turbo** | 25/25 | **19.14 s** | **21.11 GiB** | ✅ | Very good; fewer visual errors than FLUX in our review | **Strong candidate** |
| **Qwen-Image-2.1 — Diffusers run** | 25/25 | **49.64 s** | **16.95 GiB** | Not final serving path | Strong quality; closest measured run to the ~16 GB target | Candidate evidence only |
| **Qwen-Image-2.1 — vLLM-Omni** | 🔄 25-run benchmark now running | TBD | TBD | ✅ | API smoke test successful | **Strong candidate** |
| **OmniGen2** | Smoke test | ~6.08 s wall time | ~23.26 GiB observed | ✅ | Acceptable image; weak generated text | Feasibility only |

> **Important:** VRAM figures should be compared together with the runtime configuration. Measurements from different serving paths are not automatically equivalent.

---

## 5. 1024×1024 Follow-Up Tests

1024×1024 is a useful follow-up test for quality and scaling behavior, but the minimum required open-source benchmark remains 512×512.

| Model | Result | Avg Latency | Peak VRAM | Status |
|---|---:|---:|---:|---|
| **FLUX.2 Klein 4B** | 25/25 | **16.91 s** | **19.46 GiB** | ✅ Complete |
| **Stable Diffusion 3.5 Medium** | 25/25 | **4.09 s** | **20.39 GiB** | ✅ Complete |
| **Qwen-Image-2.1 — Diffusers run** | 25/25 | **77.47 s** | **16.95 GiB** | ✅ Complete |
| **Z-Image-Turbo** | — | — | — | ⏳ Planned if time permits |

---

# 6. Key Engineering Finding — Qwen-Image-2.1 on vLLM-Omni

Qwen-Image-2.1 initially failed to start through the existing vLLM-Omni image with:

```text
Model class QwenImage21Pipeline not found in diffusion model registry
```

## Root Cause

The existing vLLM-Omni build did not contain the `QwenImage21Pipeline` implementation required by Qwen-Image-2.1.

## Resolution

We:

1. Checked the latest vLLM-Omni source.
2. Located the Qwen-Image-2.1 implementation in the dedicated upstream PR branch.
3. Verified that the branch registers `QwenImage21Pipeline`.
4. Installed the compatible vLLM 0.29.0 CUDA build.
5. Started Qwen-Image-2.1 through `vllm serve --omni`.
6. Verified that the vLLM-Omni API server started successfully.
7. Sent a real request to `/v1/images/generations` and received a generated image successfully.

### Current vLLM-Omni Serving Status

**✅ Qwen-Image-2.1 is now successfully serving through vLLM-Omni.**

Observed during startup:

- `QwenImage21Pipeline` detected successfully
- Model loaded successfully
- Pure diffusion API server initialized
- `/v1/images/generations` available
- Application startup completed
- One 512×512 API smoke request completed in approximately **7 seconds end-to-end**
- vLLM-Omni reported approximately **30.55 GiB GPU memory after model loading** in the current configuration

### Why This Matters

This removes the major technical blocker that previously prevented Qwen-Image-2.1 from being considered for the final vLLM/vLLM-Omni deployment requirement.

The **full 25-prompt benchmark through the vLLM-Omni API is now running** so that final latency and VRAM measurements come from the actual serving path.

---

# 7. Current Shortlist

## Leading Candidates

### Z-Image-Turbo
**Why it remains strong:**

- 25/25 successful benchmark
- Good visual quality in our review
- Fewer visible generation errors than FLUX in our tested outputs
- vLLM-Omni serving demonstrated
- Reasonable deployment path

**Main trade-off:**

- 21.11 GiB peak VRAM in the recorded 512 run
- ~19.14 s average latency

### Qwen-Image-2.1
**Why it is now strong:**

- 25/25 successful 512 benchmark through Diffusers
- Strong image quality in our review
- Previous benchmark reached ~16.95 GiB peak VRAM
- Qwen vLLM-Omni compatibility issue has now been solved
- Real vLLM-Omni API generation succeeded

**Current questions being validated:**

- Final 25-prompt vLLM-Omni latency
- Final vLLM-Omni peak VRAM
- Whether runtime optimization is needed to approach the ~16 GB target
- Final license suitability for the intended deployment scenario

### Stable Diffusion 3.5 Medium
Kept as a strong engineering fallback because it is highly reliable and significantly faster than the other tested candidates, although the measured VRAM is above the target environment.

---

# 8. Models Not Selected for the Current Final Shortlist

## SDXL Base 1.0

Technically efficient in the tested configuration, but the generated outputs showed unacceptable prompt adherence / visual quality. A diagnostic FP32 test did not resolve the tested output problem.

**Engineering conclusion:** exclude the tested SDXL serving configuration rather than spend final-project time optimizing a candidate that currently fails the quality requirement.

## OmniGen2

Successfully loaded and generated an image, but only a smoke test was completed. Generated text quality was weaker, and we already have stronger candidates with more complete benchmark evidence.

---

# 9. Benchmark Evidence Collected

For benchmarked models we record, where applicable:

- `run_id`
- `prompt_id`
- `prompt`
- `category`
- `model`
- `width`
- `height`
- `generation_time_seconds`
- `peak_vram`
- `GPU`
- `success`
- `error`
- `image_path`
- `timestamp`
- runtime settings such as seed / steps / guidance

This allows the final model choice to be justified using measured evidence rather than assumptions.

---

# 10. Current Project Status

```text
Commercial benchmark              ██████████ 100% ✅
Commercial evaluation             ██████████ 100% ✅
OSS feasibility testing            █████████░  90% 🔄
Final candidate validation         ████████░░  80% 🔄
vLLM/Omni serving validation       █████████░  90% 🔄
Final 512 benchmarks               ████████░░  80% 🔄
Authenticated final API            ███░░░░░░░  30% 🔄
Side-by-side human evaluation      ██░░░░░░░░  20% ⏳
Final report & presentation        ████░░░░░░  40% 🔄
```

> Percentages are a progress communication aid, not formal project scoring.

---

# 11. What We Are Doing Right Now

### Current Task
Run the **full 25-prompt 512×512 benchmark for Qwen-Image-2.1 through the working vLLM-Omni HTTP API**.

### Goal
Replace the previous standalone Diffusers performance numbers with measurements from the actual serving stack that can be used for final deployment evaluation.

### Success Criteria

- 25/25 prompts complete successfully
- 25 images saved
- Average / median / min / max latency calculated
- Peak VRAM captured
- No serving failures
- Image quality reviewed

---

# 12. Immediate Next Steps

1. **Finish Qwen vLLM-Omni 25-prompt benchmark**
2. **Summarize Qwen latency + VRAM + reliability**
3. **Compare Qwen vs Z vs SD3.5 using the official selection criteria**
4. **Confirm the final two models**
5. **Containerize / finalize Kubernetes inference services**
6. **Add Bearer-token or API-key authentication**
7. **Run the final side-by-side human evaluation**
8. **Complete final benchmark comparison and recommendation**
9. **Finish technical report and presentation**

### Optional if time remains

- Test Z-Image-Turbo at 1024×1024
- Explore runtime / VRAM optimization for Qwen
- LoRA experimentation only if core project requirements are already complete

---

# 13. Quick Presentation Summary

## What have we completed?

- Built the fixed 25-prompt commercial benchmark
- Completed the commercial-model benchmark and evaluation
- Tested multiple open-source image models
- Collected latency, VRAM, reliability, and image outputs
- Excluded SDXL based on measured quality problems in the tested configuration
- Identified Z-Image-Turbo and Qwen-Image-2.1 as leading candidates
- Diagnosed and solved the Qwen-Image-2.1 vLLM-Omni compatibility blocker
- Successfully generated an image through the Qwen vLLM-Omni HTTP API

## Where are we now?

**Final candidate validation and deployment benchmarking.**

The Qwen-Image-2.1 25-prompt vLLM-Omni benchmark is currently running.

## What is next?

Finalize the two models, add authenticated production-style endpoints, complete side-by-side human evaluation, and finish the final report.

---

# 14. Current Technical Takeaway

The project has moved beyond simply proving that open-source models can generate images.

We are now comparing **deployable inference services** using measurable engineering criteria:

**quality + prompt adherence + latency + VRAM + reliability + serving compatibility + deployment complexity.**

The strongest current progress is the successful transition of **Qwen-Image-2.1 from standalone experimentation to working vLLM-Omni API serving**, removing a key blocker before final model selection.

