import csv
import random
import html
from collections import defaultdict

INPUT = "evaluation_input.csv"
OUTPUT_HTML = "blind_preference.html"
OUTPUT_MAPPING = "blind_preference_mapping.csv"

# same random seed to ensure reproducibility
rng = random.Random(2026)

# read the input CSV file
with open(INPUT, "r", encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

# collect images by prompt_id
groups = defaultdict(list)

for row in rows:
    groups[row["prompt_id"]].append(row)

mapping_rows = []
sections = []

for prompt_id in sorted(groups.keys()):
    images = groups[prompt_id]

    if len(images) != 3:
        print(f"WARNING: {prompt_id} has {len(images)} images instead of 3")
        continue

    # random order A/B/C for each prompt
    rng.shuffle(images)

    prompt = images[0]["prompt"]

    image_cards = []
    options = []

    for label, row in zip(["A", "B", "C"], images):
        image_id = row["image_id"]
        image_url = row["image_url"]
        if "/benchmark/" in image_url:
            image_url = "../benchmark/" + image_url.split("/benchmark/", 1)[1]

        mapping_rows.append({
            "prompt_id": prompt_id,
            "label": label,
            "image_id": image_id
        })

        image_cards.append(f"""
        <div class="card">
            <h3>Image {label}</h3>
            <img src="{html.escape(image_url, quote=True)}">
        </div>
        """)

        options.append(
            f'<option value="{html.escape(image_id)}">{label}</option>'
        )

    sections.append(f"""
    <section>
        <h2>{html.escape(prompt_id)}</h2>

        <p class="prompt">
            {html.escape(prompt)}
        </p>

        <div class="images">
            {''.join(image_cards)}
        </div>

        <label>
           Which image is best for marketing?
        </label>

        <select class="choice" data-prompt="{html.escape(prompt_id)}">
            <option value="">-- Choose --</option>
            {''.join(options)}
            <option value="TIE"> Tie </option>
        </select>
    </section>
    """)

# حفظ الـ mapping
with open(OUTPUT_MAPPING, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["prompt_id", "label", "image_id"]
    )
    writer.writeheader()
    writer.writerows(mapping_rows)

html_page = f"""
<!DOCTYPE html>
<html lang="ar">
<head>
<meta charset="UTF-8">

<title>Blind Image Evaluation</title>

<style>
body {{
    font-family: Arial, sans-serif;
    max-width: 1200px;
    margin: auto;
    padding: 30px;
}}

section {{
    margin-bottom: 70px;
    border-bottom: 2px solid #ddd;
    padding-bottom: 50px;
}}

.prompt {{
    font-size: 16px;
    line-height: 1.6;
}}

.images {{
    display: flex;
    gap: 20px;
    margin: 25px 0;
}}

.card {{
    flex: 1;
    text-align: center;
}}

img {{
    width: 100%;
    max-height: 420px;
    object-fit: contain;
}}

select {{
    font-size: 16px;
    padding: 8px;
    margin-left: 10px;
}}

#evaluator {{
    font-size: 16px;
    padding: 8px;
}}

button {{
    font-size: 18px;
    padding: 12px 20px;
    margin: 30px 0;
}}
</style>
</head>

<body>

<h1>Blind Commercial Image Evaluation</h1>

<p>
Read the prompt and select which image is best for marketing. If you think two or more images are equally good, select "Tie".
</p>

<label>
Evaluator:
<input id="evaluator" placeholder="Person1">
</label>

{''.join(sections)}

<button onclick="downloadCSV()">Save Results as CSV</button>

<script>

function csvEscape(value) {{
    value = String(value ?? "");
    return '"' + value.replaceAll('"', '""') + '"';
}}

function downloadCSV() {{

    const evaluator =
        document.getElementById("evaluator").value.trim();

    if (!evaluator) {{
        alert("Please enter your name first");
        return;
    }}

    const choices =
        document.querySelectorAll(".choice");

    for (const choice of choices) {{
        if (!choice.value) {{
            alert(
                "No choice selected for prompt: "
                + choice.dataset.prompt
            );
            return;
        }}
    }}

    const rows = [
        [
            "evaluator",
            "prompt_id",
            "selected_label",
            "selected_image_id"
        ]
    ];

    choices.forEach(choice => {{

        const label =
            choice.options[
                choice.selectedIndex
            ].text;

        rows.push([
            evaluator,
            choice.dataset.prompt,
            label,
            choice.value
        ]);

    }});

    const csv =
        rows.map(
            row => row.map(csvEscape).join(",")
        ).join("\\n");

    const blob =
        new Blob([csv], {{type: "text/csv"}});

    const url =
        URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;
    a.download =
        "preference_" + evaluator + ".csv";

    a.click();

    URL.revokeObjectURL(url);
}}

</script>

</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_page)

print("Created:", OUTPUT_HTML)
print("Created:", OUTPUT_MAPPING)
print("Prompts:", len(sections))
