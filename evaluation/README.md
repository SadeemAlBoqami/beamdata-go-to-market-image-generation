# Commercial Model Evaluation

## Overview

This directory contains the Phase 2 commercial image-generation model evaluation.

The goal of this phase is to establish a commercial baseline that can later be used to compare open-source image-generation models.

Three commercial models were evaluated:

- GPT Image 2
- FLUX 2 Pro
- Gemini 3.1 Flash Image

The benchmark used:

- 25 fixed prompts
- 5 prompt categories
- 3 commercial models
- 75 generated images

The five benchmark categories are:

1. People & Lifestyle
2. Text & Typography
3. Branding & Advertising
4. Products & Physical Objects
5. Complex Compositions

---

## Evaluation Methodology

The commercial baseline combines three types of evaluation:

1. Human rubric scoring
2. Blind human preference evaluation
3. Objective benchmark measurements

This approach was selected because image-generation quality cannot be represented reliably by a single metric. The evaluation therefore considers both subjective image quality and measurable operational performance.

---

## 1. Human Rubric Evaluation

Each generated image was evaluated using a standardized 1–5 scoring framework.

The following criteria were used:

- `quality`
- `prompt_adherence`
- `composition`
- `marketing_usefulness`
- `visual_appeal`
- `text_accuracy`
- `people_anatomy`
- `object_accuracy`

### Scoring Scale

| Score | Meaning |
|---|---|
| 1 | Very poor / clear failure |
| 2 | Poor / major problems |
| 3 | Acceptable with noticeable problems |
| 4 | Good with minor issues |
| 5 | Excellent / closely satisfies the requirement |

Conditional criteria were marked as `N/A` when they were not applicable.

Examples:

- `text_accuracy` is only applicable when visible text is relevant.
- `people_anatomy` is only applicable when people are present.
- `object_accuracy` is used when specific objects, quantities, placement, or details are important.

`N/A` values are excluded from metric averages.

### Evaluation Process

Each of the 75 generated images received one complete rubric evaluation.

The same rubric and scoring scale were used consistently across all three commercial models.

The results were then aggregated:

- by model
- by prompt category
- by evaluation criterion

No single universal quality score was used. Individual dimensions are preserved so that model strengths and weaknesses remain visible.

---

## 2. Blind Human Preference Evaluation

A second human evaluation was performed using direct side-by-side comparison.

For every benchmark prompt:

- Images from the three commercial models were displayed as A, B, and C.
- Model/provider identity was hidden from evaluators.
- Evaluators selected the image they considered most suitable for marketing use.
- A `Tie` option was available.

Four evaluators independently completed all 25 prompts.

This produced:

- 25 prompts
- 4 evaluators
- 100 total preference decisions

The preference results were analyzed:

- overall by model
- by benchmark category
- with ties reported separately

This evaluation complements the rubric scoring by measuring direct human preference when all three model outputs are viewed side by side.

---

## 3. Objective Benchmark Evaluation

Objective measurements were collected from the commercial benchmark results.

The evaluated metrics include:

- generation time
- estimated cost per image
- total estimated cost
- success/failure rate
- benchmark image dimensions

Performance was summarized using:

- average generation time
- median generation time
- minimum generation time
- maximum generation time
- average cost per image
- total cost
- success rate

The same benchmark prompts were used across all three commercial models.

### Benchmark Resolution

The actual generated width and height are recorded in:

`../benchmark/results/benchmark_results.csv`

The benchmark results should be treated as the authoritative source for the image dimensions used in the commercial experiment.

---

## Output Files

### Data

`data/`

Contains the evaluation inputs and evaluator responses.

Important files include:

- `evaluation_input.csv`
- `image_mapping.csv`
- `blind_preference_mapping.csv`
- `preference_Person 1.csv`
- `preference_Person 2.csv`
- `preference_Person 3.csv`
- `preference_Person 4.csv`

### Scripts

`scripts/`

Contains scripts used to prepare and analyze the evaluation.

Important scripts include:

- `prepare_preference_evaluation.py`
- `merge_preference_results.py`
- `analyze_rubric_scores.py`
- `analyze_preference_by_category.py`
- `analyze_commercial_objective.py`
- `generate_commercial_baseline.py`

### Results

`results/`

Contains the processed evaluation outputs.

Important files include:

- `rubric_summary_by_model.csv`
- `rubric_summary_by_category.csv`
- `rubric_scores_with_models.csv`
- `preference_merged.csv`
- `preference_summary.csv`
- `preference_by_category.csv`
- `commercial_objective_summary.csv`
- `commercial_objective_by_category.csv`
- `commercial_baseline_summary.md`

The main Phase 2 output is:

`results/commercial_baseline_summary.md`

This file combines the human rubric results, blind preference results, and objective benchmark measurements into the commercial baseline.

---

## Evaluation Limitations

The commercial evaluation has several limitations that should be considered when interpreting the results:

- The benchmark contains 25 prompts and therefore represents a controlled sample rather than every possible marketing use case.
- Each individual image received one rubric evaluation, so rubric scores do not measure inter-rater agreement.
- The blind preference evaluation used four independent evaluators and provides an additional human comparison signal.
- Human image evaluation is inherently subjective.
- Commercial cost values are based on the benchmark's recorded or estimated provider costs.
- Results apply to the tested prompts, settings, and benchmark configuration.

These limitations should be considered when comparing the commercial baseline with the open-source models later in the project.

---

## Phase 2 Completion

Phase 2 is considered complete when the following outputs are available:

- 75 commercial benchmark images
- Human rubric evaluation for all images
- Blind preference evaluation from four evaluators
- Rubric analysis by model
- Rubric analysis by category
- Preference analysis by model
- Preference analysis by category
- Generation-time analysis
- Cost analysis
- Reliability analysis
- Commercial baseline summary

The completed commercial baseline will be used as the reference point for the open-source model evaluation in the next phase.
