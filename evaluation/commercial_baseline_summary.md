# Commercial Baseline Summary

## D2 — Commercial Model Evaluation

This baseline combines three evaluation dimensions: human rubric scoring, blinded human preference, and objective benchmark performance.

### Evaluation Scope

- 25 benchmark prompts
- 5 prompt categories
- 3 commercial image-generation models
- 75 generated images
- 4 blind preference evaluators
- 100 total blind preference decisions

## 1. Overall Commercial Baseline

| Model | Human Preference | Preference Rate | Avg Generation Time (s) | Avg Cost/Image (USD) | Success Rate |
|---|---:|---:|---:|---:|---:|
| flux-2-pro | 24 | 24.0% | 15.28 | $0.0315 | 100.00% |
| gemini-3.1-flash-image | 31 | 31.0% | 8.91 | $0.0670 | 100.00% |
| gpt-image-2 | 36 | 36.0% | 44.83 | $0.0500 | 100.00% |

Blind preference ties: **9 / 100**.

## 2. Human Rubric Scores by Model

| Model | Quality | Prompt Adherence | Composition | Marketing Usefulness | Visual Appeal | Text Accuracy | People / Anatomy | Object Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flux-2-pro | 4.71 | 4.33 | 4.75 | 4.42 | 4.50 | 4.32 | 4.29 | 4.35 |
| gemini-3.1-flash-image | 4.64 | 4.44 | 4.44 | 4.48 | 4.40 | 4.50 | 4.70 | 4.89 |
| gpt-image-2 | 4.77 | 4.31 | 4.54 | 4.46 | 4.62 | 4.19 | 4.80 | 4.43 |

Scores are reported separately by criterion rather than being collapsed into one overall score. N/A values are excluded from criterion averages.

## 3. Blind Human Preference by Category

| Category | flux-2-pro | gemini-3.1-flash-image | gpt-image-2 | TIE | Total |
|---|---:|---:|---:|---:|---:|
| branding_advertising | 1 | 6 | 12 | 1 | 20 |
| complex_compositions | 4 | 11 | 4 | 1 | 20 |
| people_lifestyle | 8 | 2 | 8 | 2 | 20 |
| products_objects | 6 | 5 | 5 | 4 | 20 |
| text_typography | 5 | 7 | 7 | 1 | 20 |

## 4. Objective Benchmark Performance

| Model | Attempts | Successes | Failures | Success Rate | Avg Time (s) | Median Time (s) | Min Time (s) | Max Time (s) | Avg Cost | Total Cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| flux-2-pro | 25 | 25 | 0 | 100.00% | 15.28 | 14.40 | 10.80 | 24.41 | $0.0315 | $0.7864 |
| gemini-3.1-flash-image | 25 | 25 | 0 | 100.00% | 8.91 | 9.06 | 7.56 | 9.77 | $0.0670 | $1.6750 |
| gpt-image-2 | 25 | 25 | 0 | 100.00% | 44.83 | 45.68 | 34.83 | 54.09 | $0.0500 | $1.2500 |

## 5. Objective Performance by Category

| Model | Category | Avg Time (s) | Avg Cost/Image | Success Rate |
|---|---|---:|---:|---:|
| flux-2-pro | branding_advertising | 14.21 | $0.0315 | 100.00% |
| flux-2-pro | complex_compositions | 17.84 | $0.0315 | 100.00% |
| flux-2-pro | people_lifestyle | 15.15 | $0.0315 | 100.00% |
| flux-2-pro | products_objects | 13.42 | $0.0315 | 100.00% |
| flux-2-pro | text_typography | 15.79 | $0.0315 | 100.00% |
| gemini-3.1-flash-image | branding_advertising | 9.08 | $0.0670 | 100.00% |
| gemini-3.1-flash-image | complex_compositions | 9.24 | $0.0670 | 100.00% |
| gemini-3.1-flash-image | people_lifestyle | 9.12 | $0.0670 | 100.00% |
| gemini-3.1-flash-image | products_objects | 8.87 | $0.0670 | 100.00% |
| gemini-3.1-flash-image | text_typography | 8.24 | $0.0670 | 100.00% |
| gpt-image-2 | branding_advertising | 43.10 | $0.0500 | 100.00% |
| gpt-image-2 | complex_compositions | 50.26 | $0.0500 | 100.00% |
| gpt-image-2 | people_lifestyle | 48.21 | $0.0500 | 100.00% |
| gpt-image-2 | products_objects | 40.42 | $0.0500 | 100.00% |
| gpt-image-2 | text_typography | 42.18 | $0.0500 | 100.00% |

## 6. Human Rubric Scores by Category

| Model | Category | Quality | Prompt Adherence | Composition | Marketing Usefulness | Visual Appeal | Text Accuracy | People / Anatomy | Object Accuracy |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| flux-2-pro | branding_advertising | 5.00 | 4.00 | 5.00 | 4.00 | 4.80 | 4.40 | N/A | 4.00 |
| flux-2-pro | complex_compositions | 4.75 | 4.25 | 5.00 | 4.00 | 4.75 | 4.50 | 3.50 | 4.50 |
| flux-2-pro | people_lifestyle | 4.80 | 4.60 | 4.40 | 5.00 | 4.80 | 4.33 | 4.60 | 4.20 |
| flux-2-pro | products_objects | 5.00 | 4.67 | 5.00 | 5.00 | 4.33 | 4.50 | N/A | 4.67 |
| flux-2-pro | text_typography | 3.75 | 4.00 | 4.25 | 3.75 | 3.75 | 3.67 | N/A | N/A |
| gemini-3.1-flash-image | branding_advertising | 5.00 | 4.20 | 4.80 | 4.40 | 4.80 | 3.60 | N/A | 4.60 |
| gemini-3.1-flash-image | complex_compositions | 4.67 | 4.33 | 4.17 | 4.50 | 4.67 | 4.60 | 4.50 | 5.00 |
| gemini-3.1-flash-image | people_lifestyle | 4.25 | 4.50 | 4.00 | 4.25 | 4.25 | 4.00 | 5.00 | 5.00 |
| gemini-3.1-flash-image | products_objects | 5.00 | 4.25 | 5.00 | 5.00 | 4.75 | 5.00 | N/A | 5.00 |
| gemini-3.1-flash-image | text_typography | 4.33 | 4.83 | 4.33 | 4.33 | 3.67 | 5.00 | N/A | N/A |
| gpt-image-2 | branding_advertising | 4.60 | 3.40 | 4.20 | 3.80 | 4.60 | 2.80 | N/A | 4.00 |
| gpt-image-2 | complex_compositions | 5.00 | 4.40 | 4.80 | 4.60 | 5.00 | 4.60 | 5.00 | 4.60 |
| gpt-image-2 | people_lifestyle | 5.00 | 4.33 | 5.00 | 4.50 | 4.83 | 3.67 | 4.67 | 4.40 |
| gpt-image-2 | products_objects | 5.00 | 4.40 | 4.60 | 5.00 | 4.20 | 5.00 | N/A | 4.60 |
| gpt-image-2 | text_typography | 4.20 | 5.00 | 4.00 | 4.40 | 4.40 | 5.00 | N/A | 5.00 |

## 7. Interpretation Notes

- Rubric scores use the 1–5 human evaluation scale.
- Conditional criteria such as text accuracy and people/anatomy exclude N/A values.
- Blind preference results represent direct side-by-side marketing preference from four evaluators.
- Model identity was hidden during blind preference evaluation.
- Objective metrics are calculated from the commercial benchmark runs.
- This baseline is intended for later comparison against the open-source models evaluated in subsequent project phases.
