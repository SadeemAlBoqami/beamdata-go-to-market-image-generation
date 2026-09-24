"""Blind human evaluation controls for saved benchmark outputs."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import gradio as gr


REPO_ROOT = Path(__file__).resolve().parents[2]

EVALUATION_RESULTS = (
    REPO_ROOT
    / "evaluation"
    / "data"
    / "five_model_human_evaluation.csv"
)

MODEL_LABELS = ["A", "B", "C", "D", "E"]

RUBRIC = [
    ("overall_quality", "Overall quality"),
    ("prompt_adherence", "Prompt adherence"),
    ("text_accuracy", "Text accuracy"),
    ("composition", "Composition"),
    ("marketing_usefulness", "Marketing usefulness"),
    ("visual_appeal", "Visual appeal"),
]


def build_model_evaluation(label: str) -> list:
    """Create 1–5 rubric controls for one blind model."""

    controls = []

    with gr.Accordion(
        f"Rate Model {label}",
        open=True,
    ):
        for field, title in RUBRIC:

            # Text may not exist in every benchmark prompt.
            choices = (
                ["N/A", 1, 2, 3, 4, 5]
                if field == "text_accuracy"
                else [1, 2, 3, 4, 5]
            )

            control = gr.Radio(
                choices=choices,
                label=title,
            )

            controls.append(control)

    return controls


def save_evaluation(
    evaluator_id: str,
    prompt_id: str,
    records: list[dict],
    scores: list,
) -> str:
    """Save or update one evaluator's scores for one prompt."""

    evaluator_id = (evaluator_id or "").strip()

    if not evaluator_id:
        return "Enter an evaluator ID before saving."

    if len(records) != 5:
        return "Five benchmark model outputs are required."

    expected_scores = len(MODEL_LABELS) * len(RUBRIC)

    if len(scores) != expected_scores:
        return "Evaluation form is incomplete."

    # Require every score.
    if any(score is None for score in scores):
        return "Complete all ratings before saving."

    EVALUATION_RESULTS.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fieldnames = [
        "evaluator_id",
        "prompt_id",
        "blind_label",
        "model",
        *[field for field, _ in RUBRIC],
        "timestamp",
    ]

    new_rows = []

    rubric_size = len(RUBRIC)

    for index, label in enumerate(MODEL_LABELS):

        start = index * rubric_size
        model_scores = scores[
            start:start + rubric_size
        ]

        row = {
            "evaluator_id": evaluator_id,
            "prompt_id": prompt_id,
            "blind_label": label,
            "model": records[index].get(
                "model",
                "Unknown",
            ),
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        for (
            (field, _),
            score,
        ) in zip(RUBRIC, model_scores):

            # Store N/A as blank so numerical analysis stays clean.
            row[field] = (
                ""
                if score == "N/A"
                else score
            )

        new_rows.append(row)

    # ---------------------------------------------------------
    # Update existing evaluation instead of creating duplicates.
    # ---------------------------------------------------------

    existing_rows = []

    if EVALUATION_RESULTS.is_file():

        with EVALUATION_RESULTS.open(
            newline="",
            encoding="utf-8",
        ) as source:

            existing_rows = list(
                csv.DictReader(source)
            )

    # Remove previous scores from same evaluator/prompt.
    existing_rows = [
        row
        for row in existing_rows
        if not (
            row.get("evaluator_id") == evaluator_id
            and row.get("prompt_id") == prompt_id
        )
    ]

    existing_rows.extend(new_rows)

    with EVALUATION_RESULTS.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as destination:

        writer = csv.DictWriter(
            destination,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(existing_rows)

    return (
        f"Evaluation saved for {prompt_id} "
        f"by {evaluator_id}."
    )


def load_evaluation_scores(
    evaluator_id: str,
    prompt_id: str,
) -> list:
    """Load previously saved scores for one evaluator and prompt."""

    empty_scores = [
        None
        for _ in range(
            len(MODEL_LABELS) * len(RUBRIC)
        )
    ]

    evaluator_id = (evaluator_id or "").strip()

    if not evaluator_id:
        return empty_scores

    if not EVALUATION_RESULTS.is_file():
        return empty_scores

    with EVALUATION_RESULTS.open(
        newline="",
        encoding="utf-8",
    ) as source:
        rows = list(csv.DictReader(source))

    saved_rows = {
        row["blind_label"]: row
        for row in rows
        if (
            row.get("evaluator_id") == evaluator_id
            and row.get("prompt_id") == prompt_id
        )
    }

    if not saved_rows:
        return empty_scores

    scores = []

    for label in MODEL_LABELS:
        row = saved_rows.get(label)

        if row is None:
            scores.extend(
                [None] * len(RUBRIC)
            )
            continue

        for field, _ in RUBRIC:
            value = row.get(field, "")

            if value == "":
                if field == "text_accuracy":
                    scores.append("N/A")
                else:
                    scores.append(None)
            else:
                scores.append(int(value))

    return scores