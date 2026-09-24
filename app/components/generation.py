"""Generation controls and side-by-side model results."""

from dataclasses import dataclass
from html import escape
import os
from pathlib import Path
import tempfile
from typing import Iterator
from uuid import uuid4

import gradio as gr

try:  # Supports both documented module execution and direct script execution.
    from ..services.flux_service import generate_flux
    from ..services.zimage_service import generate_zimage
except ImportError:  # pragma: no cover
    from services.flux_service import generate_flux
    from services.zimage_service import generate_zimage


# The deployed benchmarks validate 512x512. Other shapes use multiples of 16
# and may depend on the deployed backend's supported image-size settings.
ASPECT_SIZES = {
    "FLUX": {
        "Square": "1024x1024",
        "Portrait": "768x1024",
        "Story / Vertical": "576x1024",
        "Landscape": "1024x768",
    },
    "Z-Image Turbo": {
        "Square": "512x512",
        "Portrait": "384x512",
        "Story / Vertical": "288x512",
        "Landscape": "512x384",
    },
}
_DOWNLOAD_DIR = tempfile.TemporaryDirectory(prefix="beamdata-images-")


@dataclass
class ResultCardUI:
    image: gr.Image
    model: gr.Textbox
    generation_time: gr.Textbox
    resolution: gr.Textbox
    status: gr.Markdown
    peak_vram: gr.Textbox
    download: gr.DownloadButton

    def outputs(self) -> list:
        return [
            self.image, self.model, self.generation_time, self.resolution,
            self.status, self.peak_vram, self.download,
        ]


def _result_card(model_name: str, heading: str) -> ResultCardUI:
    with gr.Column(elem_classes=["result-card"]):
        gr.HTML(f"<h3>{heading}</h3>")
        image = gr.Image(
            label=f"{model_name} output", value=None, interactive=False,
            height=250, elem_classes=["result-image"],
        )
        model = gr.Textbox(label="Model", value=model_name, interactive=False)
        with gr.Row(elem_classes=["metadata-row"]):
            generation_time = gr.Textbox(label="Generation time", value="—", interactive=False)
            resolution = gr.Textbox(label="Resolution", value="—", interactive=False)
        initial_status = ("Not available in current deployment" if model_name == "Qwen Image"
                          else "Not generated")
        status = gr.Markdown(f"<span class='status-pill neutral'>{initial_status}</span>")
        with gr.Accordion("Technical details", open=False):
            peak_vram = gr.Textbox(label="Peak VRAM", value="—", interactive=False)
        download = gr.DownloadButton("Download image", value=None, interactive=False)
    return ResultCardUI(image, model, generation_time, resolution, status, peak_vram, download)


def _card_values(
    model_name: str, image=None, generation_time: str = "—", resolution: str = "—",
    status: str = "Not generated", status_class: str = "neutral",
    peak_vram: str = "—", download_path: str | None = None,
) -> list:
    return [
        image, model_name, generation_time, resolution,
        f"<span class='status-pill {status_class}'>{escape(status)}</span>",
        peak_vram, gr.update(value=download_path, interactive=download_path is not None),
    ]


def _active_status(flux_selected: bool, zimage_selected: bool) -> str:
    names = [
        name for name, selected in (("FLUX", flux_selected), ("Z-Image Turbo", zimage_selected))
        if selected
    ]
    if not names:
        return "Active: None selected"
    return "  •  ".join(
        f"Active: {name} • "
        + ("Endpoint not configured" if name == "Z-Image Turbo" and not os.environ.get("ZIMAGE_ENDPOINT")
           else "Ready to generate")
        for name in names
    )


def _save_for_download(image, model_name: str) -> str:
    path = Path(_DOWNLOAD_DIR.name) / f"{model_name.lower().replace(' ', '-')}-{uuid4().hex}.png"
    image.save(path, format="PNG")
    return str(path)


def _generate_selected(
    prompt: str, flux_selected: bool, zimage_selected: bool, aspect_ratio: str,
) -> Iterator[list]:
    """Stream visible states while calling only selected model services."""
    selected = {"FLUX": bool(flux_selected), "Z-Image Turbo": bool(zimage_selected)}
    values = {
        name: _card_values(name, status="Not selected" if not selected[name] else "Not generated")
        for name in selected
    }
    qwen = _card_values("Qwen Image", status="Not available in current deployment")

    def output(message: str) -> list:
        return [message, *values["FLUX"], *values["Z-Image Turbo"], *qwen]

    if not prompt or not prompt.strip():
        yield output("Enter a prompt to generate images.")
        return
    if not any(selected.values()):
        yield output("Select FLUX or Z-Image Turbo to generate an image.")
        return

    for model_name, service in (("FLUX", generate_flux), ("Z-Image Turbo", generate_zimage)):
        if not selected[model_name]:
            continue
        values[model_name] = _card_values(model_name, status="Loading model...", status_class="pending")
        yield output(f"Loading model... {model_name}")
        values[model_name] = _card_values(model_name, status="Generating image...", status_class="pending")
        yield output(f"Generating image... {model_name}")

        size = ASPECT_SIZES[model_name][aspect_ratio]
        result = service(prompt.strip(), size=size)
        if result.success and result.image is not None:
            try:
                download_path = _save_for_download(result.image, model_name)
            except OSError:
                download_path = None
            width, height = result.image.size
            peak_vram = f"{result.peak_vram:.0f} MB" if result.peak_vram is not None else "—"
            values[model_name] = _card_values(
                model_name, image=result.image,
                generation_time=f"{result.generation_time:.2f} s",
                resolution=f"{width} × {height}",
                status="Success", status_class="success",
                peak_vram=peak_vram, download_path=download_path,
            )
            message = f"{model_name} image generated successfully."
            if download_path is None:
                message += " Download is temporarily unavailable."
        else:
            values[model_name] = _card_values(
                model_name, generation_time=f"{result.generation_time:.2f} s",
                status=f"Generation failed: {result.error or 'Backend unavailable.'}",
                status_class="failure",
            )
            message = f"Generation failed for {model_name}. See its card for details."
        yield output(message)


def build_generation_section() -> None:
    """Render the Generate tab, including a disabled Qwen control and card."""
    prompt = gr.Textbox(
        label="Marketing prompt",
        placeholder="Example: A premium product hero image for a sustainable skincare launch…",
        lines=3,
    )
    gr.HTML("<p class='control-label'>Models to compare</p>")
    with gr.Row(elem_classes=["model-controls"]):
        flux = gr.Checkbox(label="FLUX", value=True)
        zimage = gr.Checkbox(label="Z-Image Turbo", value=True)
        gr.Checkbox(label="Qwen Image — Not Available in Current Deployment",
                    value=False, interactive=False)
    active = gr.Markdown(_active_status(True, True), elem_classes=["active-models"])
    flux.change(_active_status, inputs=[flux, zimage], outputs=active)
    zimage.change(_active_status, inputs=[flux, zimage], outputs=active)
    aspect_ratio = gr.Dropdown(
        choices=list(ASPECT_SIZES["FLUX"]), value="Square", label="Aspect ratio",
    )
    generate_button = gr.Button("Generate images", variant="primary", elem_classes=["generate-button"])
    status = gr.Markdown("<span class='status-note'>Choose a prompt and generate with the active models.</span>")

    with gr.Row(equal_height=True, elem_classes=["results-grid"]):
        cards = [
            _result_card("FLUX", "FLUX"),
            _result_card("Z-Image Turbo", "Z-Image Turbo"),
            _result_card("Qwen Image", "Qwen Image — Not Available in Current Deployment"),
        ]
    outputs = [status, *(component for card in cards for component in card.outputs())]
    generate_button.click(
        _generate_selected, inputs=[prompt, flux, zimage, aspect_ratio], outputs=outputs,
    )
