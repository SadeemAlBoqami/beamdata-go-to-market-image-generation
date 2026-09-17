import csv
import glob
from collections import Counter

# 4 evaluator files to merge
files = [
    "preference_Person 1.csv",
    "preference_Person 2.csv",
    "preference_Person 3.csv",
    "preference_Person 4.csv",
]

# link each image_id to its provider and model
mapping = {}

with open("image_mapping.csv", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        mapping[row["image_id"]] = {
            "provider": row["provider"],
            "model": row["model"]
        }

merged = []

for filename in files:
    with open(filename, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):

            image_id = row["selected_image_id"]

            if image_id == "TIE":
                provider = "TIE"
                model = "TIE"
            else:
                info = mapping.get(image_id, {})
                provider = info.get("provider", "")
                model = info.get("model", "")

            merged.append({
                "evaluator": row["evaluator"],
                "prompt_id": row["prompt_id"],
                "selected_label": row["selected_label"],
                "selected_image_id": image_id,
                "provider": provider,
                "model": model,
            })

# complete the merged results and write to a new CSV file
with open("preference_merged.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "evaluator",
            "prompt_id",
            "selected_label",
            "selected_image_id",
            "provider",
            "model",
        ]
    )
    writer.writeheader()
    writer.writerows(merged)

# Summary of how many times each model was selected
counts = Counter(row["model"] for row in merged)

with open("preference_summary.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["model", "times_selected"])

    for model, count in counts.items():
        writer.writerow([model, count])

print(f"Merged {len(files)} evaluator files.")
print(f"Total choices: {len(merged)}")
print("Results:", dict(counts))
