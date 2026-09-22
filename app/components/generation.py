"""Generation controls and placeholder comparison cards."""

from dataclasses import dataclass
from html import escape
from typing import Sequence

import gradio as gr

try:  # Supports both `python -m app.app` and `python app/app.py`.
    from ..services.flux_service import generate_flux
except ImportError:  # pragma: no cover - convenience for direct execution
    from services.flux_service import generate_flux


MODELS = ("FLUX", "Z-Image Turbo", "Qwen Image")


@dataclass
class GenerationUI:
    """Components used to connect future generation backends to the UI."""

    prompt: gr.Textbox
    models: gr.CheckboxGroup
    generate_button: gr.Button
    status: gr.Markdown
    cards: list["ResultCardUI"]


@dataclass
class ResultCardUI:
    """Dynamic components belonging to one model's comparison card."""

    image: gr.Image
    generation_time: gr.Textbox
    peak_vram: gr.Textbox
    status: gr.Markdown


def _result_card(model_name: str) -> ResultCardUI:
    """Build one empty result card and return its dynamic components."""
    with gr.Column(elem_classes=["result-card"]):
        gr.HTML(f"<h3>{model_name}</h3>")
        image = gr.Image(
            label=f"{model_name} output",
            value=None,
            interactive=False,
            height=250,
            elem_classes=["result-image"],
        )
        with gr.Row(elem_classes=["metadata-row"]):
            generation_time = gr.Textbox(label="Generation time", value="—", interactive=False)
            peak_vram = gr.Textbox(label="Peak VRAM", value="—", interactive=False)
        status = gr.Markdown("<span class='status-pill neutral'>Not generated</span>")
    return ResultCardUI(image, generation_time, peak_vram, status)


def _card_state(
    image=None,
    generation_time: str = "—",
    peak_vram: str = "—",
    status: str = "<span class='status-pill neutral'>Not generated</span>",
) -> list[object]:
    return [image, generation_time, peak_vram, status]


def _generate_selected(prompt: str, selected_models: Sequence[str] | None) -> list[object]:
    """Generate only selected FLUX output; leave other backends as placeholders."""
    selected = set(selected_models or [])
    if not prompt or not prompt.strip():
        state = _card_state(status="<span class='status-pill neutral'>Awaiting prompt</span>")
        return ["Please enter a prompt before preparing a comparison.", *state, *state, *state]

    outputs: list[object] = []
    messages: list[str] = []
    for model_name in MODELS:
        if model_name == "FLUX" and model_name in selected:
            result = generate_flux(prompt.strip())
            if result.success:
                outputs.extend(
                    _card_state(
                        image=result.image,
                        generation_time=f"{result.generation_time:.2f} s",
                        status="<span class='success-message'>Success</span>",
                    )
                )
                messages.append("FLUX image generated successfully.")
            else:
                error = escape(result.error or "Unknown error")
                outputs.extend(
                    _card_state(status=f"<span class='validation-message'>Failed: {error}</span>")
                )
                messages.append("FLUX generation failed. See the FLUX card for details.")
        elif model_name in selected:
            outputs.extend(_card_state(status="<span class='status-pill pending'>Integration pending</span>"))
        else:
            outputs.extend(_card_state(status="<span class='status-pill neutral'>Not selected</span>"))

    if "FLUX" not in selected:
        messages.append("FLUX was not selected, so its backend was not called.")
    return [" ".join(messages), *outputs]


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
        cards = [_result_card(model_name) for model_name in MODELS]

    card_outputs = [component for card in cards for component in (
        card.image, card.generation_time, card.peak_vram, card.status
    )]
    generate_button.click(_generate_selected, inputs=[prompt, models], outputs=[status, *card_outputs])
    return GenerationUI(prompt, models, generate_button, status, cards)
