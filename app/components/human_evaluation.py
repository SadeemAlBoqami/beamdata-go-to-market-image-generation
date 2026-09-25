"""Pairwise human preference review of already-saved benchmark images."""

from html import escape
from itertools import combinations

import gradio as gr

try:
    from ..services.benchmark_service import load_comparison, load_prompt_choices
    from .evaluation import RUBRIC, load_pairwise_evaluation, save_pairwise_evaluation
except ImportError:  # pragma: no cover - direct script execution
    from services.benchmark_service import load_comparison, load_prompt_choices
    from evaluation import RUBRIC, load_pairwise_evaluation, save_pairwise_evaluation


SCORE_COUNT = 2 * len(RUBRIC)


def _pairs(records: list[dict]) -> list[tuple[str, str]]:
    available = [index for index, record in enumerate(records) if record.get("success")]
    return [
        (f"{records[a]['model']} vs {records[b]['model']}", f"{a}:{b}")
        for a, b in combinations(available, 2)
    ]


def _selected(prompt_id: str, pair_id: str):
    prompt, records = load_comparison(prompt_id)
    if pair_id not in {value for _, value in _pairs(records)}:
        return prompt, None, None
    a, b = (int(index) for index in pair_id.split(":"))
    return prompt, records[a], records[b]


def _view(prompt_id: str, pair_id: str | None, evaluator_id: str) -> list:
    try:
        prompt, records = load_comparison(prompt_id)
        choices = _pairs(records)
    except (OSError, ValueError, KeyError):
        prompt, records, choices = "Saved benchmark data is unavailable.", [], []
    valid = {value for _, value in choices}
    if pair_id not in valid:
        pair_id = choices[0][1] if choices else None
    pair_update = gr.update(choices=choices, value=pair_id)
    progress = (
        f"Comparison {next(i for i, (_, value) in enumerate(choices) if value == pair_id) + 1}"
        f" of {len(choices)} for {prompt_id}"
        if pair_id else "No saved image pair available for this prompt."
    )
    if pair_id is None:
        return [pair_update, progress, prompt, "<h3>Image A</h3>", None,
                "<h3>Image B</h3>", None, None, *([None] * SCORE_COUNT)]
    a, b = (int(index) for index in pair_id.split(":"))
    image_a, image_b = records[a], records[b]
    try:
        saved = load_pairwise_evaluation(evaluator_id, prompt_id, image_a, image_b)
    except (OSError, ValueError):
        saved = [None] * (1 + SCORE_COUNT)
    return [
        pair_update, progress, prompt,
        f"<h3>Image A · {escape(image_a['model'])}</h3>", image_a["image"],
        f"<h3>Image B · {escape(image_b['model'])}</h3>", image_b["image"],
        *saved,
    ]


def _prompt_view(prompt_id: str, evaluator_id: str) -> list:
    return _view(prompt_id, None, evaluator_id)


def _save(evaluator_id: str, prompt_id: str, pair_id: str, preference: str, *scores) -> str:
    try:
        prompt, image_a, image_b = _selected(prompt_id, pair_id)
        if image_a is None or image_b is None:
            return "Select a comparison with two saved images."
        return save_pairwise_evaluation(
            evaluator_id, prompt_id, prompt, image_a, image_b, preference, list(scores),
        )
    except (OSError, ValueError, KeyError):
        return "Evaluation could not be saved. Check that evaluation storage is writable."


def _adjacent(prompt_id: str, pair_id: str, direction: int) -> tuple[str, str]:
    ids = [value for _, value in load_prompt_choices()]
    if prompt_id not in ids:
        return prompt_id, pair_id
    position = ids.index(prompt_id)
    try:
        _, records = load_comparison(prompt_id)
        options = [value for _, value in _pairs(records)]
    except (OSError, ValueError, KeyError):
        options = []
    if pair_id in options:
        next_index = options.index(pair_id) + direction
        if 0 <= next_index < len(options):
            return prompt_id, options[next_index]
    next_prompt_index = position + direction
    while 0 <= next_prompt_index < len(ids):
        next_id = ids[next_prompt_index]
        try:
            _, records = load_comparison(next_id)
            next_options = [value for _, value in _pairs(records)]
        except (OSError, ValueError, KeyError):
            next_options = []
        if next_options:
            return next_id, next_options[0 if direction > 0 else -1]
        next_prompt_index += direction
    return prompt_id, pair_id


def _navigate(prompt_id: str, pair_id: str, evaluator_id: str, direction: int) -> list:
    next_prompt, next_pair = _adjacent(prompt_id, pair_id, direction)
    message = "Comparison loaded." if (next_prompt, next_pair) != (prompt_id, pair_id) else "No more comparisons."
    return [next_prompt, message, *_view(next_prompt, next_pair, evaluator_id)]


def _previous(prompt_id: str, pair_id: str, evaluator_id: str) -> list:
    return _navigate(prompt_id, pair_id, evaluator_id, -1)


def _next(prompt_id: str, pair_id: str, evaluator_id: str) -> list:
    return _navigate(prompt_id, pair_id, evaluator_id, 1)


def _save_and_next(
    evaluator_id: str, prompt_id: str, pair_id: str, preference: str, *scores,
) -> list:
    result = _save(evaluator_id, prompt_id, pair_id, preference, *scores)
    if not result.startswith("Evaluation saved"):
        return [gr.skip(), result, *([gr.skip()] * (8 + SCORE_COUNT))]
    next_prompt, next_pair = _adjacent(prompt_id, pair_id, 1)
    if (next_prompt, next_pair) == (prompt_id, pair_id):
        result += " All comparisons are complete."
    return [next_prompt, result, *_view(next_prompt, next_pair, evaluator_id)]


def build_human_evaluation_section(dashboard: gr.Blocks) -> None:
    """Show exactly two named saved outputs and persist A/B/Tie decisions."""
    choices = load_prompt_choices()
    if not choices:
        gr.Markdown("Saved benchmark prompts are unavailable.")
        return

    with gr.Row():
        evaluator_id = gr.Textbox(label="Evaluator ID", placeholder="Example: E01")
        prompt_id = gr.Dropdown(
            choices=choices, value=choices[0][1], label="Benchmark prompt",
        )
    pair_id = gr.Dropdown(label="Comparison")
    progress = gr.Markdown()
    prompt_text = gr.Textbox(label="Saved prompt", lines=4, interactive=False)

    with gr.Row(equal_height=True, elem_classes=["evaluation-grid"]):
        with gr.Column(elem_classes=["result-card", "evaluation-card"]):
            name_a = gr.HTML("<h3>Image A</h3>")
            image_a = gr.Image(label="Image A", interactive=False, height=320)
        with gr.Column(elem_classes=["result-card", "evaluation-card"]):
            name_b = gr.HTML("<h3>Image B</h3>")
            image_b = gr.Image(label="Image B", interactive=False, height=320)

    preference = gr.Radio(["A", "B", "Tie"], label="Which image is better?")
    scores = []
    with gr.Accordion("Detailed scoring (optional)", open=False):
        with gr.Row(elem_classes=["evaluation-grid"]):
            for side in ("A", "B"):
                with gr.Column():
                    gr.Markdown(f"Image {side}")
                    for field, title in RUBRIC:
                        options = ["N/A", 1, 2, 3, 4, 5] if field == "text_accuracy" else [1, 2, 3, 4, 5]
                        scores.append(gr.Radio(options, label=f"{side} · {title}"))

    with gr.Row(elem_classes=["evaluation-actions"]):
        previous = gr.Button("← Previous comparison")
        next_button = gr.Button("Next comparison →")
        save = gr.Button("Save Evaluation")
        save_next = gr.Button("Save & Next", variant="primary")
    confirmation = gr.Markdown("Choose A, B, or Tie to save a preference.")

    view_outputs = [
        pair_id, progress, prompt_text, name_a, image_a, name_b, image_b,
        preference, *scores,
    ]
    nav_outputs = [prompt_id, confirmation, *view_outputs]
    prompt_id.input(
        _prompt_view, inputs=[prompt_id, evaluator_id], outputs=view_outputs,
    )
    pair_id.input(
        _view, inputs=[prompt_id, pair_id, evaluator_id], outputs=view_outputs,
    )
    evaluator_id.change(
        _view, inputs=[prompt_id, pair_id, evaluator_id], outputs=view_outputs,
    )
    previous.click(
        _previous, inputs=[prompt_id, pair_id, evaluator_id], outputs=nav_outputs,
    )
    next_button.click(
        _next, inputs=[prompt_id, pair_id, evaluator_id], outputs=nav_outputs,
    )
    save.click(
        _save, inputs=[evaluator_id, prompt_id, pair_id, preference, *scores],
        outputs=confirmation,
    )
    save_next.click(
        _save_and_next,
        inputs=[evaluator_id, prompt_id, pair_id, preference, *scores],
        outputs=nav_outputs,
    )
    dashboard.load(
        _prompt_view, inputs=[prompt_id, evaluator_id], outputs=view_outputs,
    )
