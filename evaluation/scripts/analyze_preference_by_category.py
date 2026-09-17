import csv
from collections import defaultdict, Counter

PREFERENCE_FILE = "preference_merged.csv"
BENCHMARK_FILE = "../benchmark/results/benchmark_results.csv"
OUTPUT_FILE = "preference_by_category.csv"


# 1) prompt_id -> category
prompt_categories = {}

with open(BENCHMARK_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        prompt_id = row["prompt_id"]
        category = row.get("category", "").strip()

        if prompt_id and category:
            prompt_categories[prompt_id] = category


# 2) Count selections by category
results = defaultdict(Counter)

with open(PREFERENCE_FILE, encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        prompt_id = row["prompt_id"]
        model = row.get("model", "").strip()

        category = prompt_categories.get(prompt_id, "Unknown")

        if not model:
            model = "Unknown"

        results[category][model] += 1


# 3) Collect all model names
all_models = set()

for counts in results.values():
    all_models.update(counts.keys())

# Put Tie last if present
models = sorted(m for m in all_models if m != "TIE")

if "TIE" in all_models:
    models.append("TIE")


# 4) Write CSV
with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    fieldnames = ["category"] + models + ["total"]

    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for category in sorted(results):
        row = {"category": category}

        total = 0

        for model in models:
            count = results[category][model]
            row[model] = count
            total += count

        row["total"] = total

        writer.writerow(row)


# 5) Print summary
print("Done.")
print(f"Created: {OUTPUT_FILE}")
print()

grand_total = 0

for category in sorted(results):
    print(category)

    category_total = 0

    for model in models:
        count = results[category][model]
        print(f"  {model}: {count}")
        category_total += count

    print(f"  Total: {category_total}")
    print()

    grand_total += category_total

print(f"Grand total: {grand_total}")
