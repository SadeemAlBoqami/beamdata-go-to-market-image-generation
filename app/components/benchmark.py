"""Saved five-model benchmark comparison and human evaluation."""

import gradio as gr

try:
    from ..services.benchmark_service import (
        load_comparison,
        load_prompt_choices,
    )
except ImportError:  # pragma: no cover
    from services.benchmark_service import (
        load_comparison,
        load_prompt_choices,
    )

try:
    from .evaluation import (
        MODEL_LABELS,
        RUBRIC,
        build_model_evaluation,
        save_evaluation,
        load_evaluation_scores,
    )
except ImportError:  # pragma: no cover
    from evaluation import (
        MODEL_LABELS,
        RUBRIC,
        build_model_evaluation,
        save_evaluation,
        load_evaluation_scores,
    )


def _prompt_ids() -> list[str]:
    """Return benchmark prompt IDs in their original order."""

    return [
        value
        for _, value in load_prompt_choices()
    ]


def _progress_text(prompt_id: str) -> str:
    """Return current prompt progress."""

    ids = _prompt_ids()

    if prompt_id not in ids:
        return "### Progress: —"

    current = ids.index(prompt_id) + 1

    return f"### Progress: {current} / {len(ids)}"


def _previous_prompt(prompt_id: str) -> str:
    """Return previous prompt ID."""

    ids = _prompt_ids()

    if prompt_id not in ids:
        return ids[0]

    index = ids.index(prompt_id)

    if index == 0:
        return ids[0]

    return ids[index - 1]


def _next_prompt(prompt_id: str) -> str:
    """Return next prompt ID."""

    ids = _prompt_ids()

    if prompt_id not in ids:
        return ids[0]

    index = ids.index(prompt_id)

    if index >= len(ids) - 1:
        return ids[-1]

    return ids[index + 1]


def _record_values(record: dict) -> list:
    """Convert one saved benchmark record into UI values."""

    success = record.get("success", False)

    generation_time = record.get("generation_time")

    if generation_time not in (None, "—"):
        generation_time = f"{float(generation_time):.2f} s"
    else:
        generation_time = "—"

    cost = record.get("cost")

    if cost not in (None, "—"):
        cost = f"${float(cost):.4f}"
    else:
        cost = "—"

    return [
        record.get("image"),
        "Success" if success else "Saved output unavailable",
        generation_time,
        record.get("resolution", "—"),
        cost,
        record.get("model", "—"),
    ]


def _display_prompt(
    prompt_id: str,
    evaluator_id: str,
):
    """
    Load the five saved images and any scores already saved
    by this evaluator for this prompt.
    """

    try:
        prompt, records = load_comparison(prompt_id)

    except (OSError, ValueError, KeyError):
        prompt = "Saved benchmark data is unavailable."
        records = [{} for _ in MODEL_LABELS]

    records = list(records[:5])

    while len(records) < 5:
        records.append({})

    display_values = []

    for record in records:
        display_values.extend(
            _record_values(record)
        )

    scores = load_evaluation_scores(
        evaluator_id,
        prompt_id,
    )

    return [
        _progress_text(prompt_id),
        prompt,
        *display_values,
        *scores,
    ]


def _save_current_evaluation(
    evaluator_id: str,
    prompt_id: str,
    *scores,
):
    """Save ratings for the currently displayed prompt."""

    try:
        _, records = load_comparison(prompt_id)

    except (OSError, ValueError, KeyError):
        return "Saved benchmark data is unavailable."

    if len(records) != 5:
        return "All five benchmark outputs are required."

    if not all(
        record.get("success")
        for record in records
    ):
        return (
            "All five saved outputs must be "
            "available before saving."
        )

    return save_evaluation(
        evaluator_id=evaluator_id,
        prompt_id=prompt_id,
        records=records,
        scores=list(scores),
    )


def _go_previous(
    prompt_id: str,
    evaluator_id: str,
):
    """Move to previous prompt and load its saved evaluation."""

    previous_id = _previous_prompt(prompt_id)

    return [
        previous_id,
        "Previous prompt loaded.",
        *_display_prompt(
            previous_id,
            evaluator_id,
        ),
    ]


def _save_and_next(
    evaluator_id: str,
    prompt_id: str,
    *scores,
):
    """Save current ratings and move to the next prompt."""

    result = _save_current_evaluation(
        evaluator_id,
        prompt_id,
        *scores,
    )

    # Validation failed.
    # Stay on same prompt and keep current unsaved scores.
    if not result.startswith("Evaluation saved"):

        current_display = _display_prompt(
            prompt_id,
            evaluator_id,
        )

        score_count = (
            len(MODEL_LABELS)
            * len(RUBRIC)
        )

        # Keep the ratings currently entered by the user
        # instead of resetting them.
        current_display[-score_count:] = list(scores)

        return [
            prompt_id,
            result,
            *current_display,
        ]

    ids = _prompt_ids()
    current_index = ids.index(prompt_id)

    # Last prompt
    if current_index == len(ids) - 1:

        return [
            prompt_id,
            (
                f"{result} "
                f"All {len(ids)} prompts are complete."
            ),
            *_display_prompt(
                prompt_id,
                evaluator_id,
            ),
        ]

    next_id = _next_prompt(prompt_id)

    return [
        next_id,
        result,
        *_display_prompt(
            next_id,
            evaluator_id,
        ),
    ]


def _saved_card(label: str):
    """Build one blind image card with evaluation controls."""

    with gr.Column(
        elem_classes=["result-card"],
    ):

        gr.HTML(
            f"<h3>Image {label}</h3>"
        )

        image = gr.Image(
            label=f"Saved output {label}",
            interactive=False,
            height=300,
        )

        status = gr.Textbox(
            label="Status",
            interactive=False,
        )

        # Keep technical information hidden by default
        # so it does not bias human evaluation.
        with gr.Accordion(
            "Technical details",
            open=False,
        ):

            generation_time = gr.Textbox(
                label="Generation time",
                interactive=False,
            )

            resolution = gr.Textbox(
                label="Resolution",
                interactive=False,
            )

            cost = gr.Textbox(
                label="Cost (if recorded)",
                interactive=False,
            )

        # Model name stays hidden unless manually revealed.
        with gr.Accordion(
            "Reveal model identity",
            open=False,
        ):

            model = gr.Textbox(
                label="Model",
                interactive=False,
            )

        # Human evaluation controls.
        ratings = build_model_evaluation(label)

    display_components = [
        image,
        status,
        generation_time,
        resolution,
        cost,
        model,
    ]

    return display_components, ratings


def build_benchmark_section(
    dashboard: gr.Blocks,
) -> None:
    """Render five saved outputs and persistent human evaluation."""

    choices = load_prompt_choices()

    if not choices:
        gr.Markdown(
            "Saved benchmark prompts are unavailable."
        )
        return

    # ---------------------------------------------------------
    # Evaluator + prompt selection
    # ---------------------------------------------------------

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

    progress = gr.Markdown(
        _progress_text(choices[0][1])
    )

    prompt_text = gr.Textbox(
        label="Saved prompt",
        lines=5,
        interactive=False,
    )

    gr.Markdown(
        """
        Compare the five saved outputs blindly.

        Rate each image from **1–5**.
        Text Accuracy may be marked **N/A**
        when the prompt does not require text.
        """
    )

    cards = []

    # ---------------------------------------------------------
    # Images A, B, C
    # ---------------------------------------------------------

    with gr.Row(
        equal_height=True,
        elem_classes=["results-grid"],
    ):

        for label in MODEL_LABELS[:3]:
            cards.append(
                _saved_card(label)
            )

    # ---------------------------------------------------------
    # Images D, E
    # ---------------------------------------------------------

    with gr.Row(
        equal_height=True,
        elem_classes=["results-grid"],
    ):

        for label in MODEL_LABELS[3:]:
            cards.append(
                _saved_card(label)
            )

    display_outputs = [
        component
        for display_components, _ in cards
        for component in display_components
    ]

    score_inputs = [
        control
        for _, ratings in cards
        for control in ratings
    ]

    # ---------------------------------------------------------
    # Navigation
    # ---------------------------------------------------------

    with gr.Row():

        previous_button = gr.Button(
            "← Previous",
            variant="secondary",
        )

        save_button = gr.Button(
            "Save Evaluation",
            variant="secondary",
        )

        save_next_button = gr.Button(
            "Save & Next →",
            variant="primary",
        )

    confirmation = gr.Markdown(
        "Complete the ratings for all five images."
    )

    # ---------------------------------------------------------
    # User manually selects a prompt
    # ---------------------------------------------------------

    prompt_id.input(
        _display_prompt,
        inputs=[
            prompt_id,
            evaluator_id,
        ],
        outputs=[
            progress,
            prompt_text,
            *display_outputs,
            *score_inputs,
        ],
    )

    # ---------------------------------------------------------
    # Evaluator changes
    # Reload that evaluator's saved scores if they exist.
    # ---------------------------------------------------------

    evaluator_id.change(
        _display_prompt,
        inputs=[
            prompt_id,
            evaluator_id,
        ],
        outputs=[
            progress,
            prompt_text,
            *display_outputs,
            *score_inputs,
        ],
    )

    # ---------------------------------------------------------
    # Previous
    # ---------------------------------------------------------

    previous_button.click(
        _go_previous,
        inputs=[
            prompt_id,
            evaluator_id,
        ],
        outputs=[
            prompt_id,
            confirmation,
            progress,
            prompt_text,
            *display_outputs,
            *score_inputs,
        ],
    )

    # ---------------------------------------------------------
    # Save only
    # ---------------------------------------------------------

    save_button.click(
        _save_current_evaluation,
        inputs=[
            evaluator_id,
            prompt_id,
            *score_inputs,
        ],
        outputs=confirmation,
    )

    # ---------------------------------------------------------
    # Save + go to next prompt
    # ---------------------------------------------------------

    save_next_button.click(
        _save_and_next,
        inputs=[
            evaluator_id,
            prompt_id,
            *score_inputs,
        ],
        outputs=[
            prompt_id,
            confirmation,
            progress,
            prompt_text,
            *display_outputs,
            *score_inputs,
        ],
    )

    # ---------------------------------------------------------
    # Initial load
    # ---------------------------------------------------------

    dashboard.load(
        _display_prompt,
        inputs=[
            prompt_id,
            evaluator_id,
        ],
        outputs=[
            progress,
            prompt_text,
            *display_outputs,
            *score_inputs,
        ],
    )