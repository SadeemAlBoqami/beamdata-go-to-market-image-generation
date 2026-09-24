"""Saved two-model benchmark comparison; never runs inference."""

import gradio as gr

try:
    from ..services.benchmark_service import load_comparison, load_prompt_choices
except ImportError:  # pragma: no cover
    from services.benchmark_service import load_comparison, load_prompt_choices


def _display_prompt(prompt_id: str):
    try:
        prompt, records = load_comparison(prompt_id)
    except (OSError, ValueError, KeyError):
        return [
            "Saved benchmark data is unavailable.", *([None, "Unavailable", "—", "—", "—", "—"] * 2),
            None, "Saved benchmark data is unavailable.",
        ]
    values = [prompt]
    for record in records:
        success = record.get("success", False)
        values.extend([
            record.get("image"),
            "Success" if success else "Saved output unavailable",
            f"{float(record['generation_time']):.2f} s" if record.get("generation_time") not in (None, "—") else "—",
            record.get("resolution", "—"),
            f"${float(record['cost']):.4f}" if record.get("cost") not in (None, "—") else "—",
            record.get("model", "—"),
        ])
    return [*values, None, "Select A, B, or Tie to record a session preference."]


def _submit_preference(preference: str | None, prompt_id: str) -> str:
    if preference is None:
        return "Select A, B, or Tie before submitting."
    try:
        _, records = load_comparison(prompt_id)
    except (OSError, ValueError, KeyError):
        return "Saved benchmark data is unavailable."
    if len(records) != 2 or not all(record.get("success") for record in records):
        return "Both saved outputs must be available before submitting a preference."
    return "Preference received for this session. It has not been saved to a dataset."


def _saved_card(label: str) -> list:
    with gr.Column(elem_classes=["result-card"]):
        gr.HTML(f"<h3>Model {label}</h3>")
        image = gr.Image(label=f"Saved output {label}", interactive=False, height=300)
        status = gr.Textbox(label="Status", interactive=False)
        with gr.Row(elem_classes=["metadata-row"]):
            generation_time = gr.Textbox(label="Generation time", interactive=False)
            resolution = gr.Textbox(label="Resolution", interactive=False)
        cost = gr.Textbox(label="Cost (if recorded)", interactive=False)
        with gr.Accordion("Reveal model identity", open=False):
            model = gr.Textbox(label="Model", interactive=False)
    return [image, status, generation_time, resolution, cost, model]


def build_benchmark_section(dashboard: gr.Blocks) -> None:
    """Render saved outputs, metadata, and an unsaved blind preference."""
    choices = load_prompt_choices()
    if not choices:
        gr.Markdown("Saved benchmark prompts are unavailable.")
        return

    prompt_id = gr.Dropdown(
        choices=choices, value=choices[0][1], label="Benchmark prompt",
    )
    prompt_text = gr.Textbox(label="Saved prompt", lines=5, interactive=False)
    with gr.Row(equal_height=True, elem_classes=["results-grid"]):
        card_a = _saved_card("A")
        card_b = _saved_card("B")
    gr.Markdown("Compare the saved images as A and B. Model identities are hidden in collapsed details.")
    preference = gr.Radio(choices=["A", "B", "Tie"], label="Direct preference")
    submit = gr.Button("Submit preference", variant="secondary")
    confirmation = gr.Markdown("Preferences are validated in this session only.")

    outputs = [prompt_text, *card_a, *card_b, preference, confirmation]
    prompt_id.change(_display_prompt, inputs=prompt_id, outputs=outputs)
    submit.click(_submit_preference, inputs=[preference, prompt_id], outputs=confirmation)
    # Display the selected prompt on first load without making an inference request.
    dashboard.load(_display_prompt, inputs=prompt_id, outputs=outputs)
