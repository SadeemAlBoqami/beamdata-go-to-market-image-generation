import csv

FILES = {
    "rubric_model": "rubric_summary_by_model.csv",
    "rubric_category": "rubric_summary_by_category.csv",
    "preference_summary": "preference_summary.csv",
    "preference_category": "preference_by_category.csv",
    "objective_summary": "commercial_objective_summary.csv",
    "objective_category": "commercial_objective_by_category.csv",
}

OUTPUT = "commercial_baseline_summary.md"


def read_csv(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def fmt(value, decimals=2):
    if value is None or value == "":
        return "N/A"

    try:
        return f"{float(value):.{decimals}f}"
    except ValueError:
        return value


# -----------------------
# Load data
# -----------------------

rubric_model = read_csv(FILES["rubric_model"])
rubric_category = read_csv(FILES["rubric_category"])
preference_summary = read_csv(FILES["preference_summary"])
preference_category = read_csv(FILES["preference_category"])
objective_summary = read_csv(FILES["objective_summary"])
objective_category = read_csv(FILES["objective_category"])


# -----------------------
# Build lookup tables
# -----------------------

rubric_by_model = {
    row["model"]: row
    for row in rubric_model
}

objective_by_model = {
    row["model"]: row
    for row in objective_summary
}

preference_by_model = {}

for row in preference_summary:
    model = row.get("model", "")
    count = (
        row.get("times_selected")
        or row.get("count")
        or row.get("selections")
        or "0"
    )

    preference_by_model[model] = int(float(count))


# Total human preference decisions
total_preferences = sum(preference_by_model.values())

# Models only — exclude TIE
models = [
    model for model in objective_by_model
    if model.upper() != "TIE"
]


# -----------------------
# Start Markdown
# -----------------------

lines = []

lines.append("# Commercial Baseline Summary")
lines.append("")
lines.append("## D2 — Commercial Model Evaluation")
lines.append("")
lines.append(
    "This baseline combines three evaluation dimensions: "
    "human rubric scoring, blinded human preference, and objective "
    "benchmark performance."
)
lines.append("")

lines.append("### Evaluation Scope")
lines.append("")
lines.append("- 25 benchmark prompts")
lines.append("- 5 prompt categories")
lines.append("- 3 commercial image-generation models")
lines.append("- 75 generated images")
lines.append("- 4 blind preference evaluators")
lines.append(f"- {total_preferences} total blind preference decisions")
lines.append("")


# -----------------------
# Overall snapshot
# -----------------------

lines.append("## 1. Overall Commercial Baseline")
lines.append("")

lines.append(
    "| Model | Human Preference | Preference Rate | "
    "Avg Generation Time (s) | Avg Cost/Image (USD) | "
    "Success Rate |"
)

lines.append(
    "|---|---:|---:|---:|---:|---:|"
)

for model in models:
    objective = objective_by_model[model]

    count = preference_by_model.get(model, 0)

    rate = (
        count / total_preferences * 100
        if total_preferences else 0
    )

    lines.append(
        f"| {model} "
        f"| {count} "
        f"| {rate:.1f}% "
        f"| {fmt(objective.get('avg_generation_time_seconds'))} "
        f"| ${fmt(objective.get('avg_cost_usd'), 4)} "
        f"| {fmt(objective.get('success_rate_percent'))}% |"
    )

lines.append("")

tie_count = preference_by_model.get(
    "TIE",
    preference_by_model.get("Tie", 0)
)

lines.append(
    f"Blind preference ties: **{tie_count} / {total_preferences}**."
)
lines.append("")


# -----------------------
# Rubric by model
# -----------------------

lines.append("## 2. Human Rubric Scores by Model")
lines.append("")

metrics = [
    "quality",
    "prompt_adherence",
    "composition",
    "marketing_usefulness",
    "visual_appeal",
    "text_accuracy",
    "people_anatomy",
    "object_accuracy",
]

pretty_metrics = {
    "quality": "Quality",
    "prompt_adherence": "Prompt Adherence",
    "composition": "Composition",
    "marketing_usefulness": "Marketing Usefulness",
    "visual_appeal": "Visual Appeal",
    "text_accuracy": "Text Accuracy",
    "people_anatomy": "People / Anatomy",
    "object_accuracy": "Object Accuracy",
}

header = "| Model | " + " | ".join(
    pretty_metrics[m] for m in metrics
) + " |"

separator = "|---|" + "---:|" * len(metrics)

lines.append(header)
lines.append(separator)

for model in models:
    row = rubric_by_model.get(model, {})

    values = [
        fmt(row.get(metric))
        for metric in metrics
    ]

    lines.append(
        f"| {model} | " +
        " | ".join(values) +
        " |"
    )

lines.append("")
lines.append(
    "Scores are reported separately by criterion rather than being "
    "collapsed into one overall score. N/A values are excluded from "
    "criterion averages."
)
lines.append("")


# -----------------------
# Preference by category
# -----------------------

lines.append("## 3. Blind Human Preference by Category")
lines.append("")

if preference_category:
    pref_columns = list(preference_category[0].keys())

    model_columns = [
        c for c in pref_columns
        if c not in {"category", "total"}
    ]

    lines.append(
        "| Category | " +
        " | ".join(model_columns) +
        " | Total |"
    )

    lines.append(
        "|---|" +
        "---:|" * len(model_columns) +
        "---:|"
    )

    for row in preference_category:
        values = [
            row.get(col, "0")
            for col in model_columns
        ]

        lines.append(
            f"| {row['category']} | " +
            " | ".join(values) +
            f" | {row.get('total', '')} |"
        )

lines.append("")


# -----------------------
# Objective performance
# -----------------------

lines.append("## 4. Objective Benchmark Performance")
lines.append("")

lines.append(
    "| Model | Attempts | Successes | Failures | "
    "Success Rate | Avg Time (s) | Median Time (s) | "
    "Min Time (s) | Max Time (s) | Avg Cost | Total Cost |"
)

lines.append(
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
)

for model in models:
    row = objective_by_model[model]

    lines.append(
        f"| {model} "
        f"| {row.get('attempts', '')} "
        f"| {row.get('successes', '')} "
        f"| {row.get('failures', '')} "
        f"| {fmt(row.get('success_rate_percent'))}% "
        f"| {fmt(row.get('avg_generation_time_seconds'))} "
        f"| {fmt(row.get('median_generation_time_seconds'))} "
        f"| {fmt(row.get('min_generation_time_seconds'))} "
        f"| {fmt(row.get('max_generation_time_seconds'))} "
        f"| ${fmt(row.get('avg_cost_usd'), 4)} "
        f"| ${fmt(row.get('total_cost_usd'), 4)} |"
    )

lines.append("")


# -----------------------
# Performance by category
# -----------------------

lines.append("## 5. Objective Performance by Category")
lines.append("")

lines.append(
    "| Model | Category | Avg Time (s) | "
    "Avg Cost/Image | Success Rate |"
)

lines.append(
    "|---|---|---:|---:|---:|"
)

for row in objective_category:
    lines.append(
        f"| {row.get('model', '')} "
        f"| {row.get('category', '')} "
        f"| {fmt(row.get('avg_generation_time_seconds'))} "
        f"| ${fmt(row.get('avg_cost_usd'), 4)} "
        f"| {fmt(row.get('success_rate_percent'))}% |"
    )

lines.append("")


# -----------------------
# Rubric by category
# -----------------------

lines.append("## 6. Human Rubric Scores by Category")
lines.append("")

lines.append(
    "| Model | Category | Quality | Prompt Adherence | "
    "Composition | Marketing Usefulness | Visual Appeal | "
    "Text Accuracy | People / Anatomy | Object Accuracy |"
)

lines.append(
    "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"
)

for row in rubric_category:
    lines.append(
        f"| {row.get('model', '')} "
        f"| {row.get('category', '')} "
        f"| {fmt(row.get('quality'))} "
        f"| {fmt(row.get('prompt_adherence'))} "
        f"| {fmt(row.get('composition'))} "
        f"| {fmt(row.get('marketing_usefulness'))} "
        f"| {fmt(row.get('visual_appeal'))} "
        f"| {fmt(row.get('text_accuracy'))} "
        f"| {fmt(row.get('people_anatomy'))} "
        f"| {fmt(row.get('object_accuracy'))} |"
    )

lines.append("")


# -----------------------
# Methodology note
# -----------------------

lines.append("## 7. Interpretation Notes")
lines.append("")
lines.append(
    "- Rubric scores use the 1–5 human evaluation scale."
)
lines.append(
    "- Conditional criteria such as text accuracy and people/anatomy "
    "exclude N/A values."
)
lines.append(
    "- Blind preference results represent direct side-by-side marketing "
    "preference from four evaluators."
)
lines.append(
    "- Model identity was hidden during blind preference evaluation."
)
lines.append(
    "- Objective metrics are calculated from the commercial benchmark runs."
)
lines.append(
    "- This baseline is intended for later comparison against the "
    "open-source models evaluated in subsequent project phases."
)
lines.append("")


# -----------------------
# Save
# -----------------------

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))


print("Done.")
print(f"Created: {OUTPUT}")
print(f"Models included: {len(models)}")
print(f"Blind preference decisions: {total_preferences}")

