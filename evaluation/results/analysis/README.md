# Analysis

This folder contains the processed benchmark and evaluation outputs used for the final comparison between the commercial and open-source image-generation models.

## Contents

### Objective Benchmark Analysis

- `Objective_Benchmark_Analysis__Objective_Summary.csv`
  Summary of latency, reliability, VRAM, resolution, and cost-related metrics.

- `Objective_Benchmark_Analysis__Category_Latency.csv`
  Average generation latency by benchmark prompt category.

- `Objective_Benchmark_Analysis__Normalized_Data.csv`
  Normalized benchmark records combining the evaluated models into a common structure.

- `Objective_Benchmark_Analysis__Inputs_Notes.csv`
  Analysis notes and remaining inputs, including the GPU hourly cost required for self-hosted cost-per-image estimation.

### Final Comparison Analysis

- `Final_Comparison_Analysis__Objective_Summary.csv`
  Objective benchmark summary used in the final comparison.

- `Final_Comparison_Analysis__Category_Latency.csv`
  Category-level latency results.

- `Final_Comparison_Analysis__Normalized_Data.csv`
  Normalized benchmark data used by the final analysis.

- `Final_Comparison_Analysis__Inputs_Notes.csv`
  Assumptions, limitations, and analysis notes.

- `Final_Comparison_Analysis__Human_Eval_Raw.csv`
  Raw blinded human-ranking results across the five evaluated models.

- `Final_Comparison_Analysis__Human_Eval_Summary.csv`
  Aggregated human-evaluation results, including average rank, points, first-place share, top-2 share, and category-level performance.

- `Final_Comparison_Analysis__Final_Comparison.csv`
  Combined commercial vs. open-source comparison using benchmark and human-evaluation results.

## Evaluation Scope

The final analysis combines:

- Generation latency
- Reliability
- Peak VRAM for self-hosted models
- Commercial API cost
- Resolution
- Human preference rankings
- Category-level performance
- Deployment and infrastructure trade-offs

## Important Comparison Limitation

The open-source models were benchmarked at **512×512**, while the commercial models were benchmarked at **1024×1024**.

Therefore, latency values across these two groups should be treated as observed results and **not as a controlled 1:1 speed comparison**.

## Human Evaluation

The uploaded human-evaluation dataset contains overall blinded rankings and points for:

- FLUX.2 Klein 4B
- Z-Image Turbo
- GPT Image 2
- FLUX 2 Pro
- Gemini 3.1 Flash Image

The dataset contains ranking-based preference results only. Separate scores for prompt adherence, composition, text accuracy, or marketing usefulness are not inferred when they are not present in the source data.

## Purpose

These files support the project deliverables for:

- Performance and hardware analysis
- Commercial vs. open-source comparison
- Human evaluation
- Final technical report
- Final engineering presentation
