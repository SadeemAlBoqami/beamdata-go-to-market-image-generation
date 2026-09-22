"""Generation controls and placeholder comparison cards."""

from dataclasses import dataclass
from typing import Sequence

import gradio as gr


MODELS = ("FLUX", "Z-Image Turbo", "Qwen Image")


@dataclass
class GenerationUI:
    """Components used to connect future generation backends to the UI."""

    prompt: gr.Textbox
    models: gr.CheckboxGroup
    generate_button: gr.Button
    status: gr.Markdown
    card_statuses: list[gr.Markdown]


def _result_card(model_name: str) -> gr.Markdown:
    """Build one empty result card and return its dynamic status component."""
    with gr.Column(elem_classes=["result-card"]):
        gr.HTML(f"<h3>{model_name}</h3>")
        gr.Image(
            label=f"{model_name} output",
            value=None,
            interactive=False,
            height=250,
            elem_classes=["result-image"],
        )
        with gr.Row(elem_classes=["metadata-row"]):
            gr.Textbox(label="Generation time", value="—", interactive=False)
            gr.Textbox(label="Peak VRAM", value="—", interactive=False)
        status = gr.Markdown("<span class='status-pill neutral'>Not generated</span>")
    return status


def _prepare_generation(prompt: str, selected_models: Sequence[str] | None):
    """Report UI state only; no model service is called in this scaffold."""
    selected = set(selected_models or [])
    if not prompt or not prompt.strip():
        card_states = ["<span class='status-pill neutral'>Awaiting prompt</span>"] * len(MODELS)
        return ["Please enter a prompt before preparing a comparison.", *card_states]

    card_states = []
    for model_name in MODELS:
        if model_name in selected:
            card_states.append("<span class='status-pill pending'>Integration pending</span>")
        else:
            card_states.append("<span class='status-pill neutral'>Not selected</span>")
    return [
        "Comparison prepared. Image generation is not connected yet; no models were run.",
        *card_states,
    ]


def build_generation_section() -> GenerationUI:
    """Render model choices, static output cards, and their safe placeholder action."""
    prompt = gr.Textbox(
        label="Marketing prompt",
        placeholder="Example: A premium product hero image for a sustainable skincare launch…",
        lines=3,
    )
    models = gr.CheckboxGroup(
        choices=list(MODELS),
        value=list(MODELS),
        label="Models to compare",
        info="Choose one or more models.",
    )
    generate_button = gr.Button("Generate images", variant="primary", elem_classes=["generate-button"])
    status = gr.Markdown("<span class='status-note'>Model integration pending — outputs are intentionally empty.</span>")

    with gr.Row(equal_height=True, elem_classes=["results-grid"]):
        card_statuses = [_result_card(model_name) for model_name in MODELS]

    # Future wiring point: call the matching service only after a backend is approved.
    generate_button.click(_prepare_generation, inputs=[prompt, models], outputs=[status, *card_statuses])
    return GenerationUI(prompt, models, generate_button, status, card_statuses)
