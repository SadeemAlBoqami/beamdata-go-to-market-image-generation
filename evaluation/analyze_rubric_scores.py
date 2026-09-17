import csv
from collections import defaultdict
from statistics import mean

EVALUATION_FILE = "evaluation_input.csv"
MAPPING_FILE = "image_mapping.csv"
BENCHMARK_FILE = "../benchmark/results/benchmark_results.csv"

METRICS = [
    "quality",
    "prompt_adherence",
    "composition",
    "marketing_usefulness",
    "visual_appeal",
    "text_accuracy",
    "people_anatomy",
    "object_accuracy",
]

# ---------- helpers ----------

def parse_score(value):
    """Return score 1-5 or None for blank/N/A."""
    if value is None:
        return None

    value = value.strip()

    if value.lower() in {"", "n/a", "na", "none"}:
        return None

    try:
        score = float(value)
    except ValueError:
        return None

    if 1 <= score <= 5:
        return score

    return None


# ---------- load image -> model mapping ----------

image_mapping = {}

with open(MAPPING_FILE, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        image_mapping[row["image_id"]] = {
            "provider": row.get("provider", ""),
            "model": row.get("model", ""),
        }


# ---------- load prompt -> category mapping ----------

prompt_categories = {}

with open(BENCHMARK_FILE, encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        prompt_categories[row["prompt_id"]] = row.get("category", "")


# ---------- read evaluated images ----------

model_scores = defaultdict(lambda: defaultdict(list))
category_scores = defaultdict(lambda: defaultdict(list))

detailed_rows = []

with open(EVALUATION_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        image_id = row["image_id"]
        prompt_id = row["prompt_id"]

        mapping = image_mapping.get(image_id)

        if not mapping:
            print(f"WARNING: no mapping found for {image_id}")
            continue

        model = mapping["model"]
        provider = mapping["provider"]
        category = prompt_categories.get(prompt_id, "Unknown")

        detailed = {
            "image_id": image_id,
            "prompt_id": prompt_id,
            "category": category,
            "provider": provider,
            "model": model,
        }

        for metric in METRICS:
            score = parse_score(row.get(metric))

            detailed[metric] = "" if score is None else score

            if score is not None:
                model_scores[model][metric].append(score)
                category_scores[(model, category)][metric].append(score)

        detailed_rows.append(detailed)


# ---------- output 1: scores by model ----------

with open(
    "rubric_summary_by_model.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fields = ["model"] + METRICS
    writer = csv.DictWriter(f, fieldnames=fields)

    writer.writeheader()

    for model in sorted(model_scores):
        output = {"model": model}

        for metric in METRICS:
            values = model_scores[model][metric]

            output[metric] = (
                round(mean(values), 2)
                if values else "N/A"
            )

        writer.writerow(output)


# ---------- output 2: scores by model + category ----------

with open(
    "rubric_summary_by_category.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fields = ["model", "category"] + METRICS
    writer = csv.DictWriter(f, fieldnames=fields)

    writer.writeheader()

    for model, category in sorted(category_scores):
        output = {
            "model": model,
            "category": category,
        }

        for metric in METRICS:
            values = category_scores[(model, category)][metric]

            output[metric] = (
                round(mean(values), 2)
                if values else "N/A"
            )

        writer.writerow(output)


# ---------- output 3: joined detailed data ----------

with open(
    "rubric_scores_with_models.csv",
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fields = [
        "image_id",
        "prompt_id",
        "category",
        "provider",
        "model",
    ] + METRICS

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(detailed_rows)


print("Done.")
print(f"Evaluated images: {len(detailed_rows)}")
print("Created:")
print("- rubric_summary_by_model.csv")
print("- rubric_summary_by_category.csv")
print("- rubric_scores_with_models.csv")
