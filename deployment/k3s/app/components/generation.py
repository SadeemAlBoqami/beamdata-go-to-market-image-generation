"""Generation controls and side-by-side model results."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from html import escape
import os
from pathlib import Path
import base64
import io
import tempfile
from threading import Lock
from typing import Iterator
from uuid import uuid4

import gradio as gr

try:  # Supports both documented module execution and direct script execution.
    from ..services.flux_service import generate_flux
    from ..services.health_service import check_backend_ready
    from ..services.zimage_service import generate_zimage
except ImportError:  # pragma: no cover
    from services.flux_service import generate_flux
    from services.health_service import check_backend_ready
    from services.zimage_service import generate_zimage


# Output dimensions validated against the deployed image APIs.
ASPECT_SIZES = {
    "FLUX": {
        "Square": "512x512",
        "Portrait": "384x512",
        "Story / Vertical": "288x512",
        "Landscape": "512x384",
    },
    "Z-Image Turbo": {
        "Square": "512x512",
        "Portrait": "384x512",
        "Story / Vertical": "288x512",
        "Landscape": "512x384",
    },
}
MODELS = ("FLUX", "Z-Image Turbo")
_LOADING_HTML = (
    "<div class='image-loading' role='status' aria-live='polite'>"
    "<span class='image-loading-spinner' aria-hidden='true'></span>"
    "<strong>Generating image...</strong>"
    "<span class='image-loading-copy'>This may take a moment.</span></div>"
)
_ERROR_HTML = (
    "<div class='image-loading image-error' role='status'>"
    "<span class='image-error-icon' aria-hidden='true'>!</span>"
    "<strong>Generation failed</strong>"
    "<span class='image-loading-copy'>See the status below for details.</span></div>"
)
_DOWNLOAD_DIR = tempfile.TemporaryDirectory(prefix="beamdata-images-")
_RUN_LOCK = Lock()


@dataclass
class ActiveRun:
    id: str
    prompt: str
    flux_selected: bool
    zimage_selected: bool
    aspect_ratio: str
    started: bool = False


_ACTIVE_RUNS: dict[str, ActiveRun] = {}


@dataclass
class ResultCardUI:
    image: gr.Image
    loading: gr.HTML
    model: gr.Textbox
    generation_time: gr.Textbox
    resolution: gr.Textbox
    status: gr.Markdown
    peak_vram: gr.Textbox
    download: gr.HTML

    def outputs(self) -> list:
        return [
            self.image, self.loading, self.model, self.generation_time,
            self.resolution, self.status, self.peak_vram, self.download,
        ]


def _result_card(model_name: str) -> ResultCardUI:
    card_id = "flux-result-card" if model_name == "FLUX" else "zimage-result-card"
    with gr.Column(elem_id=card_id, elem_classes=["result-card"]):
        gr.HTML(f"<h3>{model_name}</h3>")
        gr.HTML(_LOADING_HTML, elem_classes=["instant-loading"])
        image = gr.Image(
            label=f"{model_name} output",
            value=None,
            interactive=False,
            height=250,
            elem_classes=["result-image"],
        )
        loading = gr.HTML(_LOADING_HTML, visible=False, elem_classes=["server-loading"])
        model = gr.Textbox(label="Model", value=model_name, interactive=False)
        with gr.Row(elem_classes=["metadata-row"]):
            generation_time = gr.Textbox(label="Generation time", value="—", interactive=False)
            resolution = gr.Textbox(label="Resolution", value="—", interactive=False)
        status = gr.Markdown(
            "<span class='status-pill neutral'>Ready</span>",
            elem_classes=["generation-status"],
        )
        with gr.Accordion("Technical details", open=False):
            peak_vram = gr.Textbox(label="Peak VRAM", value="—", interactive=False)
        download = gr.HTML(
            "<button disabled>Download image</button>",
            elem_classes=["image-download"],
        )
    return ResultCardUI(
        image, loading, model, generation_time, resolution, status, peak_vram, download
    )


def _status(label: str, status_class: str = "neutral") -> str:
    return f"<span class='status-pill {status_class}'>{escape(label)}</span>"


def _card_values(
    model_name: str, image=None, generation_time: str = "—", resolution: str = "—",
    status: str = "Ready", status_class: str = "neutral", peak_vram: str = "—",
    download_path: str | None = None, loading: bool = False, error: bool = False,
) -> list:
    return [
        gr.update(value=image, visible=not (loading or error)),
        gr.update(value=_ERROR_HTML if error else _LOADING_HTML, visible=loading or error),
        model_name, generation_time, resolution, _status(status, status_class),
        peak_vram, download_path or "<button disabled>Download image</button>",
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



def _download_html(image, model_name: str) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    filename = f"{model_name.lower().replace(' ', '-')}-{uuid4().hex}.png"
    return (
        f'<a href="data:image/png;base64,{encoded}" '
        f'download="{filename}" '
        f'style="display:inline-block;padding:9px 16px;'
        f'border:1px solid #d1d5db;border-radius:8px;'
        f'text-decoration:none;color:inherit;">'
        f'⬇ Download image</a>'
    )


def _finished_values(
    model_name: str, result, readiness_error: str | None = None,
) -> tuple[list, str]:
    if readiness_error:
        return (
            _card_values(model_name, status=readiness_error, status_class="failure", error=True),
            f"{model_name}: {readiness_error}.",
        )
    if result is not None and result.success and result.image is not None:
        try:
            download_path = _download_html(result.image, model_name)
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
            status_class="failure", error=True,
        ),
        f"Generation failed for {model_name}. See its card for details.",
    )


def _session_key(request: gr.Request | None) -> str:
    return request.session_hash if request and request.session_hash else "local-session"


def _run_is_current(session: str, run_id: str) -> bool:
    with _RUN_LOCK:
        run = _ACTIVE_RUNS.get(session)
        return run is not None and run.id == run_id


def _start_generation(
    prompt: str, flux_selected: bool, zimage_selected: bool, aspect_ratio: str,
    request: gr.Request | None = None,
) -> list:
    """Atomically reserve one run and show card loaders before any backend call."""
    session = _session_key(request)
    skipped = [value for _ in MODELS for value in _skip_card()]
    with _RUN_LOCK:
        if session in _ACTIVE_RUNS:
            return [gr.skip(), *skipped, gr.update(value="Generating...", interactive=False)]

        selected = {"FLUX": bool(flux_selected), "Z-Image Turbo": bool(zimage_selected)}
        if not prompt or not prompt.strip():
            return ["Enter a prompt to generate images.", *skipped,
                    gr.update(value="Generate", interactive=True)]
        if not any(selected.values()):
            return ["Select FLUX or Z-Image Turbo to generate an image.", *skipped,
                    gr.update(value="Generate", interactive=True)]
        _ACTIVE_RUNS[session] = ActiveRun(
            id=uuid4().hex, prompt=prompt.strip(),
            flux_selected=bool(flux_selected), zimage_selected=bool(zimage_selected),
            aspect_ratio=aspect_ratio,
        )

    cards = [
        _card_values(name, status="Generating...", status_class="pending", loading=True)
        if selected[name] else _skip_card("Not selected")
        for name in MODELS
    ]
    return [
        "Generating selected images...", *(value for card in cards for value in card),
        gr.update(value="Generating...", interactive=False),
    ]


def _run_model(name: str, service, prompt: str, size: str):
    readiness_error = check_backend_ready(name)
    if readiness_error:
        return None, readiness_error
    return service(prompt, size=size), None


def _generate_selected(request: gr.Request | None = None) -> Iterator[list]:
    """Run each selected backend once and restore the button after all finish."""
    session = _session_key(request)
    with _RUN_LOCK:
        run = _ACTIVE_RUNS.get(session)
        if run is None or run.started:
            return
        run.started = True
        run_id = run.id

    selected = {
        name: service for name, enabled, service in (
            ("FLUX", run.flux_selected, generate_flux),
            ("Z-Image Turbo", run.zimage_selected, generate_zimage),
        ) if enabled
    }

    def output(message: str, name: str, card: list, button=gr.skip()) -> list:
        updates = {model: card if model == name else _skip_card() for model in MODELS}
        return [message, *(value for model in MODELS for value in updates[model]), button]

    try:
        with ThreadPoolExecutor(max_workers=len(selected)) as executor:
            futures = {
                executor.submit(
                    _run_model, name, service, run.prompt,
                    ASPECT_SIZES[name][run.aspect_ratio],
                ): name
                for name, service in selected.items()
            }
            remaining = len(futures)
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result, readiness_error = future.result()
                except Exception:
                    result, readiness_error = None, "Backend unavailable"
                if not _run_is_current(session, run_id):
                    return

                card, message = _finished_values(name, result, readiness_error)
                remaining -= 1
                if remaining == 0:
                    with _RUN_LOCK:
                        if _ACTIVE_RUNS.get(session) is run:
                            del _ACTIVE_RUNS[session]
                    button = gr.update(value="Generate", interactive=True)
                else:
                    button = gr.skip()
                yield output(message, name, card, button)
    except Exception:
        if _run_is_current(session, run_id):
            yield [
                "Generation failed. Please try again.",
                *(value for _ in MODELS for value in _skip_card()),
                gr.update(value="Generate", interactive=True),
            ]
    finally:
        with _RUN_LOCK:
            if _ACTIVE_RUNS.get(session) is run:
                del _ACTIVE_RUNS[session]


def build_generation_section() -> None:
    """Render the two live result cards and an informational Qwen badge."""
    prompt = gr.Textbox(
        label="Marketing prompt",
        placeholder="Example: A premium product hero image for a sustainable skincare launch…",
        lines=3,
    )
    gr.HTML("<p class='control-label'>Models to compare</p>")
    with gr.Row(elem_classes=["model-controls"]):
        flux = gr.Checkbox(label="FLUX.2 Klein", value=True)
        zimage = gr.Checkbox(label="Z-Image Turbo", value=True)
    gr.HTML("<p class='qwen-note'>Qwen Image — Not Available in Current Deployment</p>")
    active = gr.Markdown(_active_status(True, True), elem_classes=["active-models"])
    flux.change(_active_status, inputs=[flux, zimage], outputs=active)
    zimage.change(_active_status, inputs=[flux, zimage], outputs=active)
    aspect_ratio = gr.Dropdown(
        choices=list(ASPECT_SIZES["FLUX"]), value="Square", label="Aspect ratio",
    )
    generate_button = gr.Button(
        "Generate", variant="primary", elem_id="generate-button",
        elem_classes=["generate-button"],
    )
    status = gr.Markdown("<span class='status-note'>Choose a prompt and generate with the active models.</span>")

    with gr.Row(equal_height=True, elem_classes=["results-grid"]):
        cards = [_result_card(name) for name in MODELS]
    outputs = [status, *(component for card in cards for component in card.outputs()), generate_button]
    inputs = [prompt, flux, zimage, aspect_ratio]
    prepare = generate_button.click(
        _start_generation, inputs=inputs, outputs=outputs,
        queue=False, show_progress="hidden", trigger_mode="once",
        js="""async (prompt, flux, zimage, aspect) => {
            const root = document.getElementById("generate-button");
            const button = root?.matches("button") ? root : root?.querySelector("button");
            if (button) {
                button.disabled = true;
                button.textContent = "Generating...";
            }
            if (prompt?.trim() && aspect && (flux || zimage)) {
                for (const [id, selected] of [
                    ["flux-result-card", flux], ["zimage-result-card", zimage]
                ]) {
                    if (!selected) continue;
                    const card = document.getElementById(id);
                    if (!card) continue;
                    const status = () => card.querySelector(".generation-status .status-pill")?.textContent;
                    const previousStatus = status();
                    const observer = new MutationObserver(() => {
                        if (status() && status() !== previousStatus) {
                            observer.disconnect();
                            requestAnimationFrame(() => requestAnimationFrame(() => {
                                card.classList.remove("client-generating");
                            }));
                        }
                    });
                    observer.observe(card, {childList: true, characterData: true, subtree: true});
                    card.classList.add("client-generating");
                }
                await new Promise((resolve) => {
                    requestAnimationFrame(() => requestAnimationFrame(resolve));
                    setTimeout(resolve, 120);
                });
            }
            return [prompt, flux, zimage, aspect];
        }""",
    )
    prepare.then(
        _generate_selected, outputs=outputs, show_progress="hidden",
        trigger_mode="once",
    )
