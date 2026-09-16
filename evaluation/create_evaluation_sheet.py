import csv

INPUT = "../benchmark/results/benchmark_results.csv"
EVALUATION_OUTPUT = "evaluation_input.csv"
MAPPING_OUTPUT = "image_mapping.csv"

rows = []

with open(INPUT, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        success = str(row.get("success", "")).strip().lower()

        if success in {"true", "1", "yes"}:
            rows.append(row)

# Fixed order
rows.sort(key=lambda r: (
    r.get("prompt_id", ""),
    r.get("provider", "")
))

mapping_rows = []
evaluation_rows = []

for i, row in enumerate(rows, start=1):
    image_id = f"IMG{i:03d}"

    prompt_id = row.get("prompt_id", "")
    prompt = row.get("prompt", "")
    provider = row.get("provider", "")
    model = row.get("model", "")

    # Supports `image_url` or an image reference if the name is different
    image_ref = (
        row.get("image_url")
        or row.get("image_reference")
        or row.get("image_path")
        or ""
    )

    mapping_rows.append({
        "image_id": image_id,
        "prompt_id": prompt_id,
        "provider": provider,
        "model": model,
        "image_url": image_ref,
    })

    evaluation_rows.append({
        "image_id": image_id,
        "prompt_id": prompt_id,
        "prompt": prompt,
        "image_url": image_ref,
        "quality": "",
        "prompt_adherence": "",
        "composition": "",
        "marketing_usefulness": "",
        "visual_appeal": "",
        "text_accuracy": "",
        "people_anatomy": "",
        "object_accuracy": "",
        "notes": "",
    })

with open(MAPPING_OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "image_id",
            "prompt_id",
            "provider",
            "model",
            "image_url",
        ]
    )
    writer.writeheader()
    writer.writerows(mapping_rows)

with open(EVALUATION_OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "image_id",
            "prompt_id",
            "prompt",
            "image_url",
            "quality",
            "prompt_adherence",
            "composition",
            "marketing_usefulness",
            "visual_appeal",
            "text_accuracy",
            "people_anatomy",
            "object_accuracy",
            "notes",
        ]
    )
    writer.writeheader()
    writer.writerows(evaluation_rows)

print(f"Created {EVALUATION_OUTPUT} with {len(evaluation_rows)} images.")
print(f"Created {MAPPING_OUTPUT}.")