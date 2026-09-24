"""Generation controls and side-by-side model results."""

from concurrent.futures import ThreadPoolExecutor, as_completed
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


# Only square generation is validated for the current deployment. Keep the
# other mappings visible for the demo, but block calls until live validation.
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
MODELS = ("FLUX", "Z-Image Turbo")
_DOWNLOAD_DIR = tempfile.TemporaryDirectory(prefix="beamdata-images-")


@dataclass
class ResultCardUI:
    image: gr.Image
    loading: gr.HTML
    model: gr.Textbox
    generation_time: gr.Textbox
    resolution: gr.Textbox
    status: gr.Markdown
    peak_vram: gr.Textbox
    download: gr.DownloadButton

    def outputs(self) -> list:
        return [
            self.image, self.loading, self.model, self.generation_time,
            self.resolution, self.status, self.peak_vram, self.download,
        ]


def _result_card(model_name: str) -> ResultCardUI:
    with gr.Column(elem_classes=["result-card"]):
        gr.HTML(f"<h3>{model_name}</h3>")
        image = gr.Image(
            label=f"{model_name} output", value=None, interactive=False,
            height=250, elem_classes=["result-image"],
        )
        loading = gr.HTML(
            "<div class='image-loading' role='status' aria-live='polite'>"
            "<span class='image-loading-spinner' aria-hidden='true'></span>"
            "<span>Generating image...</span></div>",
            visible=False,
        )
        model = gr.Textbox(label="Model", value=model_name, interactive=False)
        with gr.Row(elem_classes=["metadata-row"]):
            generation_time = gr.Textbox(label="Generation time", value="—", interactive=False)
            resolution = gr.Textbox(label="Resolution", value="—", interactive=False)
        status = gr.Markdown("<span class='status-pill neutral'>Ready</span>")
        with gr.Accordion("Technical details", open=False):
            peak_vram = gr.Textbox(label="Peak VRAM", value="—", interactive=False)
        download = gr.DownloadButton("Download image", value=None, interactive=False)
    return ResultCardUI(
        image, loading, model, generation_time, resolution, status, peak_vram, download
    )


def _status(label: str, status_class: str = "neutral") -> str:
    return f"<span class='status-pill {status_class}'>{escape(label)}</span>"


def _card_values(
    model_name: str, image=None, generation_time: str = "—", resolution: str = "—",
    status: str = "Ready", status_class: str = "neutral", peak_vram: str = "—",
    download_path: str | None = None, loading: bool = False,
) -> list:
    return [
        gr.update(value=image, visible=not loading),
        gr.update(visible=loading),
        model_name, generation_time, resolution, _status(status, status_class),
        peak_vram, gr.update(value=download_path, interactive=download_path is not None),
    ]


def _skip_card(status: str | None = None) -> list:
    updates = [gr.skip() for _ in range(8)]
    if status is not None:
        updates[5] = _status(status)
    return updates


def _active_status(flux_selected: bool, zimage_selected: bool) -> str:
    names = [
        name for name, selected in (("FLUX", flux_selected), ("Z-Image Turbo", zimage_selected))
        if selected
    ]
    if not names:
        return "Active: None selected"
    return "  •  ".join(
        f"Active: {name} • "
        + ("Token not configured" if not os.environ.get(
            "FLUX_TOKEN" if name == "FLUX" else "ZIMAGE_TOKEN"
        ) else "Ready to generate")
        for name in names
    )


def _save_for_download(image, model_name: str) -> str:
    path = Path(_DOWNLOAD_DIR.name) / f"{model_name.lower().replace(' ', '-')}-{uuid4().hex}.png"
    image.save(path, format="PNG")
    return str(path)


def _finished_values(model_name: str, result) -> tuple[list, str]:
    if result.success and result.image is not None:
        try:
            download_path = _save_for_download(result.image, model_name)
        except OSError:
            download_path = None
        width, height = result.image.size
        peak_vram = f"{result.peak_vram:.0f} MB" if result.peak_vram is not None else "—"
        card = _card_values(
            model_name, image=result.image,
            generation_time=f"{result.generation_time:.2f} s",
            resolution=f"{width} × {height}",
            status="Success", status_class="success",
            peak_vram=peak_vram, download_path=download_path,
        )
        message = f"{model_name} image generated successfully."
        if download_path is None:
            message += " Download is temporarily unavailable."
        return card, message

    error = result.error if result is not None else "Backend unavailable."
    return (
        _card_values(
            model_name, status=f"Generation failed: {error or 'Backend unavailable.'}",
            status_class="failure",
        ),
        f"Generation failed for {model_name}. See its card for details.",
    )


def _generate_selected(
    prompt: str, flux_selected: bool, zimage_selected: bool, aspect_ratio: str,
) -> Iterator[list]:
    """Stream card-local states and independent results for selected services."""
    selected = {
        name: service for name, enabled, service in (
            ("FLUX", flux_selected, generate_flux),
            ("Z-Image Turbo", zimage_selected, generate_zimage),
        ) if enabled
    }

    def output(message: str, updates: dict[str, list]) -> list:
        return [message, *(value for name in MODELS for value in updates[name])]

    skipped = {name: _skip_card() for name in MODELS}
    if not prompt or not prompt.strip():
        yield output("Enter a prompt to generate images.", skipped)
        return
    if not selected:
        yield output("Select FLUX or Z-Image Turbo to generate an image.", skipped)
        return
    if aspect_ratio != "Square":
        yield output(
            "Only Square is validated for this deployment. Select Square to generate.",
            {name: _skip_card("Aspect ratio not yet validated") if name in selected else _skip_card()
             for name in MODELS},
        )
        return

    loading = {
        name: _card_values(name, status="Loading model...", status_class="pending", loading=True)
        if name in selected else _skip_card("Not selected")
        for name in MODELS
    }
    yield output("Loading selected model services...", loading)

    with ThreadPoolExecutor(max_workers=len(selected)) as executor:
        futures = {
            executor.submit(service, prompt.strip(), size=ASPECT_SIZES[name][aspect_ratio]): name
            for name, service in selected.items()
        }
        generating = {
            name: _card_values(name, status="Generating...", status_class="pending", loading=True)
            if name in selected else _skip_card()
            for name in MODELS
        }
        yield output("Generating selected images...", generating)

        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
            except Exception:
                result = None
            card, message = _finished_values(name, result)
            updates = {model: card if model == name else _skip_card() for model in MODELS}
            yield output(message, updates)


def build_generation_section() -> None:
    """Render the two live result cards and an informational Qwen badge."""
    prompt = gr.Textbox(
        label="Marketing prompt",
        placeholder="Example: A premium product hero image for a sustainable skincare launch…",
        lines=3,
    )
    gr.HTML("<p class='control-label'>Models to compare</p>")
    with gr.Row(elem_classes=["model-controls"]):
        flux = gr.Checkbox(label="FLUX", value=True)
        zimage = gr.Checkbox(label="Z-Image Turbo", value=True)
    gr.HTML("<p class='qwen-note'>Qwen Image — Not Available in Current Deployment</p>")
    active = gr.Markdown(_active_status(True, True), elem_classes=["active-models"])
    flux.change(_active_status, inputs=[flux, zimage], outputs=active)
    zimage.change(_active_status, inputs=[flux, zimage], outputs=active)
    aspect_ratio = gr.Dropdown(
        choices=list(ASPECT_SIZES["FLUX"]), value="Square", label="Aspect ratio",
        info="Only Square is enabled until the deployed backends pass live size checks.",
    )
    generate_button = gr.Button("Generate images", variant="primary", elem_classes=["generate-button"])
    status = gr.Markdown("<span class='status-note'>Choose a prompt and generate with the active models.</span>")

    with gr.Row(equal_height=True, elem_classes=["results-grid"]):
        cards = [_result_card(name) for name in MODELS]
    outputs = [status, *(component for card in cards for component in card.outputs())]
    generate_button.click(
        _generate_selected, inputs=[prompt, flux, zimage, aspect_ratio], outputs=outputs,
        show_progress="hidden",
    )
