"""Blind five-model ranking of already-saved benchmark images."""

import hashlib
import gradio as gr

try:
    from ..services.benchmark_service import load_comparison, load_prompt_choices
    from .evaluation import load_ranking_evaluation, save_ranking_evaluation
except ImportError:  # pragma: no cover - direct script execution
    from services.benchmark_service import load_comparison, load_prompt_choices
    from components.evaluation import (
    load_ranking_evaluation,
    save_ranking_evaluation,
)


MODEL_LABELS = ["A", "B", "C", "D", "E"]
RANK_CHOICES = [1, 2, 3, 4, 5]


def _prompt_ids() -> list[str]:
    return [value for _, value in load_prompt_choices()]


def _progress_text(prompt_id: str) -> str:
    ids = _prompt_ids()
    if prompt_id not in ids:
        return "### Progress: —"
    return f"### Progress: {ids.index(prompt_id) + 1} / {len(ids)}"


def _blind_order(evaluator_id: str, prompt_id: str, records: list[dict]) -> list[dict]:
    """Stable blind order that changes by evaluator and prompt."""
    evaluator_key = (evaluator_id or "").strip() or "anonymous"
    return sorted(
        records,
        key=lambda record: hashlib.sha256(
            (
                f"{evaluator_key}|{prompt_id}|"
                f"{record.get('model', '')}|{record.get('image', '')}"
            ).encode("utf-8")
        ).hexdigest(),
    )


def _load_ranked_records(prompt_id: str, evaluator_id: str) -> tuple[str, list[dict]]:
    prompt, records = load_comparison(prompt_id)
    records = list(records)
    if len(records) != 5:
        raise ValueError("Exactly five benchmark outputs are required.")
    return prompt, _blind_order(evaluator_id, prompt_id, records)


def _display_prompt(prompt_id: str, evaluator_id: str) -> list:
    try:
        prompt, records = _load_ranked_records(prompt_id, evaluator_id)
    except (OSError, ValueError, KeyError):
        return [
            _progress_text(prompt_id),
            "Saved benchmark data is unavailable.",
            *([None] * 5),
            *([None] * 5),
        ]

    images = [
        record.get("image") if record.get("success") else None
        for record in records
    ]

    try:
        ranks = load_ranking_evaluation(
            evaluator_id=evaluator_id,
            prompt_id=prompt_id,
            records=records,
        )
    except (OSError, ValueError, KeyError):
        ranks = [None] * 5

    return [_progress_text(prompt_id), prompt, *images, *ranks]


def _save(evaluator_id: str, prompt_id: str, *ranks) -> str:
    try:
        prompt, records = _load_ranked_records(prompt_id, evaluator_id)
    except (OSError, ValueError, KeyError):
        return "Saved benchmark data is unavailable."

    if not all(record.get("success") for record in records):
        return "All five saved benchmark images must be available before ranking."

    return save_ranking_evaluation(
        evaluator_id=evaluator_id,
        prompt_id=prompt_id,
        prompt=prompt,
        records=records,
        ranks=list(ranks),
    )


def _adjacent_prompt(prompt_id: str, direction: int) -> str:
    ids = _prompt_ids()
    if not ids:
        return prompt_id
    if prompt_id not in ids:
        return ids[0]
    index = min(max(ids.index(prompt_id) + direction, 0), len(ids) - 1)
    return ids[index]


def _navigate(prompt_id: str, evaluator_id: str, direction: int) -> list:
    next_id = _adjacent_prompt(prompt_id, direction)
    message = (
        "Prompt loaded."
        if next_id != prompt_id
        else "No more prompts in this direction."
    )
    return [next_id, message, *_display_prompt(next_id, evaluator_id)]


def _previous(prompt_id: str, evaluator_id: str) -> list:
    return _navigate(prompt_id, evaluator_id, -1)


def _next(prompt_id: str, evaluator_id: str) -> list:
    return _navigate(prompt_id, evaluator_id, 1)


def _save_and_next(evaluator_id: str, prompt_id: str, *ranks) -> list:
    result = _save(evaluator_id, prompt_id, *ranks)

    if not result.startswith("Ranking saved"):
        return [gr.skip(), result, *([gr.skip()] * 12)]

    next_id = _adjacent_prompt(prompt_id, 1)
    if next_id == prompt_id:
        result += f" All {len(_prompt_ids())} prompts are complete."
        return [prompt_id, result, *_display_prompt(prompt_id, evaluator_id)]

    return [next_id, result, *_display_prompt(next_id, evaluator_id)]


def _image_card(label: str):
    with gr.Column(elem_classes=["result-card", "evaluation-card"]):
        gr.HTML(f"<h3>Image {label}</h3>")
        image = gr.Image(
            label=f"Image {label}",
            interactive=False,
            height=300,
        )
        rank = gr.Radio(
            choices=RANK_CHOICES,
            label="Rank (1 = best, 5 = worst)",
            interactive=True,
        )
    return image, rank


def build_human_evaluation_section(dashboard: gr.Blocks) -> None:
    """Rank all five saved outputs blindly from best to worst."""
    choices = load_prompt_choices()
    if not choices:
        gr.Markdown("Saved benchmark prompts are unavailable.")
        return

    gr.Markdown(
        """
        Compare all five saved outputs **blindly** and rank them from best to worst.

        **1 = Best** · **5 = Worst** · Use each rank exactly once.

        Model identities and technical metadata are hidden during evaluation.
        """
    )

    with gr.Row():
        evaluator_id = gr.Textbox(
            label="Evaluator ID",
            placeholder="Example: E01",
        )
        prompt_id = gr.Dropdown(
            choices=choices,
            value=choices[0][1],
            label="Benchmark prompt",
        )

    progress = gr.Markdown(_progress_text(choices[0][1]))
    prompt_text = gr.Textbox(label="Saved prompt", lines=4, interactive=False)

    cards = []
    with gr.Row(equal_height=True, elem_classes=["evaluation-grid"]):
        for label in MODEL_LABELS[:3]:
            cards.append(_image_card(label))

    with gr.Row(equal_height=True, elem_classes=["evaluation-grid"]):
        for label in MODEL_LABELS[3:]:
            cards.append(_image_card(label))

    image_outputs = [image for image, _ in cards]
    rank_inputs = [rank for _, rank in cards]

    with gr.Row(elem_classes=["evaluation-actions"]):
        previous = gr.Button("← Previous prompt")
        next_button = gr.Button("Next prompt →")
        save = gr.Button("Save Ranking")
        save_next = gr.Button("Save & Next", variant="primary")

    confirmation = gr.Markdown("Assign ranks 1–5, using each rank exactly once.")

    view_outputs = [progress, prompt_text, *image_outputs, *rank_inputs]
    nav_outputs = [prompt_id, confirmation, *view_outputs]

    prompt_id.input(
        _display_prompt,
        inputs=[prompt_id, evaluator_id],
        outputs=view_outputs,
    )
    evaluator_id.change(
        _display_prompt,
        inputs=[prompt_id, evaluator_id],
        outputs=view_outputs,
    )
    previous.click(
        _previous,
        inputs=[prompt_id, evaluator_id],
        outputs=nav_outputs,
    )
    next_button.click(
        _next,
        inputs=[prompt_id, evaluator_id],
        outputs=nav_outputs,
    )
    save.click(
        _save,
        inputs=[evaluator_id, prompt_id, *rank_inputs],
        outputs=confirmation,
    )
    save_next.click(
        _save_and_next,
        inputs=[evaluator_id, prompt_id, *rank_inputs],
        outputs=nav_outputs,
    )
    dashboard.load(
        _display_prompt,
        inputs=[prompt_id, evaluator_id],
        outputs=view_outputs,
    )
