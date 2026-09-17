import csv
from collections import defaultdict
from statistics import mean, median

INPUT_FILE = "../benchmark/results/benchmark_results.csv"

OUTPUT_MODEL = "commercial_objective_summary.csv"
OUTPUT_CATEGORY = "commercial_objective_by_category.csv"


def to_float(value):
    if value is None:
        return None

    value = value.strip()

    if value == "":
        return None

    try:
        return float(value)
    except ValueError:
        return None


def is_success(row):
    status = row.get("status", "").strip().lower()

    if status:
        return status in {
            "success",
            "successful",
            "completed",
            "ok",
            "true",
            "1",
        }

    # إذا ما فيه status لكن فيه صورة نعتبر التوليد ناجح
    image_url = row.get("image_url", "").strip()
    return bool(image_url)


# -----------------------------
# Read benchmark data
# -----------------------------

with open(INPUT_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("Detected columns:")
print(", ".join(reader.fieldnames or []))
print()


# -----------------------------
# Aggregate
# -----------------------------

by_model = defaultdict(list)
by_category = defaultdict(list)

for row in rows:
    model = row.get("model", "").strip()
    category = row.get("category", "").strip()

    if not model:
        model = row.get("provider", "").strip()

    by_model[model].append(row)
    by_category[(model, category)].append(row)


def summarize(group):
    attempts = len(group)

    successful_rows = [
        row for row in group
        if is_success(row)
    ]

    successes = len(successful_rows)
    failures = attempts - successes

    success_rate = (
        successes / attempts * 100
        if attempts else 0
    )

    times = []

    for row in successful_rows:
        value = (
            row.get("generation_time_seconds")
            or row.get("latency_seconds")
            or row.get("generation_time")
            or row.get("duration_seconds")
        )

        number = to_float(value)

        if number is not None:
            times.append(number)

    costs = []

    for row in successful_rows:
        value = (
            row.get("estimated_cost_usd")
            or row.get("cost_usd")
            or row.get("estimated_cost")
        )

        number = to_float(value)

        if number is not None:
            costs.append(number)

    return {
        "attempts": attempts,
        "successes": successes,
        "failures": failures,
        "success_rate_percent": round(success_rate, 2),

        "avg_generation_time_seconds":
            round(mean(times), 2) if times else "N/A",

        "median_generation_time_seconds":
            round(median(times), 2) if times else "N/A",

        "min_generation_time_seconds":
            round(min(times), 2) if times else "N/A",

        "max_generation_time_seconds":
            round(max(times), 2) if times else "N/A",

        "avg_cost_usd":
            round(mean(costs), 4) if costs else "N/A",

        "total_cost_usd":
            round(sum(costs), 4) if costs else "N/A",

        "cost_records": len(costs),
    }


# -----------------------------
# Output by model
# -----------------------------

fields = [
    "model",
    "attempts",
    "successes",
    "failures",
    "success_rate_percent",
    "avg_generation_time_seconds",
    "median_generation_time_seconds",
    "min_generation_time_seconds",
    "max_generation_time_seconds",
    "avg_cost_usd",
    "total_cost_usd",
    "cost_records",
]

with open(
    OUTPUT_MODEL,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for model in sorted(by_model):
        result = {"model": model}
        result.update(summarize(by_model[model]))
        writer.writerow(result)


# -----------------------------
# Output by category
# -----------------------------

category_fields = ["model", "category"] + fields[1:]

with open(
    OUTPUT_CATEGORY,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=category_fields
    )

    writer.writeheader()

    for model, category in sorted(by_category):
        result = {
            "model": model,
            "category": category,
        }

        result.update(
            summarize(by_category[(model, category)])
        )

        writer.writerow(result)


print("Done.")
print(f"Total benchmark rows: {len(rows)}")
print(f"Created: {OUTPUT_MODEL}")
print(f"Created: {OUTPUT_CATEGORY}")
