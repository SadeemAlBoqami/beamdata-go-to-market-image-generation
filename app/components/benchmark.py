"""Gallery of saved official benchmark outputs; no inference or voting."""

from html import escape

import gradio as gr

try:
    from ..services.benchmark_service import load_comparison, load_prompt_choices
except ImportError:  # pragma: no cover - direct script execution
    from services.benchmark_service import load_comparison, load_prompt_choices


def _metadata(record: dict) -> str:
    """Only render fields actually present in the saved benchmark row."""
    fields = [("Model", record.get("model"))]
    if record.get("provider"):
        fields.append(("Provider", record["provider"]))
    if record.get("generation_time"):
        fields.append(("Generation time", f"{float(record['generation_time']):.2f} s"))
    if record.get("resolution"):
        fields.append(("Resolution", record["resolution"]))
    if record.get("peak_vram"):
        fields.append(("Peak VRAM", f"{float(record['peak_vram']):.0f} MiB"))
    if record.get("cost"):
        fields.append(("Estimated cost", f"${float(record['cost']):.4f}"))
    if record.get("status"):
        fields.append(("Status", record["status"]))
    details = "".join(
        f"<div><dt>{escape(label)}</dt><dd>{escape(str(value))}</dd></div>"
        for label, value in fields
    )
    return f"<dl class='benchmark-metrics'>{details}</dl>"


def _display_prompt(prompt_id: str) -> list:
    try:
        prompt, records = load_comparison(prompt_id)
    except (OSError, ValueError, KeyError):
        prompt, records = "Saved benchmark data is unavailable.", []
    values = [prompt]
    for index in range(5):
        record = records[index] if index < len(records) else {}
        values.extend([record.get("image"), _metadata(record)])
    return values


def build_benchmark_section(dashboard: gr.Blocks) -> None:
    """Read saved images and metadata; selecting a prompt never regenerates."""
    choices = load_prompt_choices()
    if not choices:
        gr.Markdown("Saved benchmark prompts are unavailable.")
        return

    prompt_id = gr.Dropdown(
        choices=choices, value=choices[0][1], label="Benchmark prompt",
    )
    prompt_text = gr.Textbox(label="Saved prompt", lines=4, interactive=False)
    gr.Markdown(
        "Official saved results, one output per available model. "
        "Commercial images are 1024×1024; the saved open-source runs are 512×512."
    )

    cards = []
    for first, last in ((0, 3), (3, 5)):
        with gr.Row(equal_height=True, elem_classes=["results-grid", "benchmark-grid"]):
            for index in range(first, last):
                with gr.Column(elem_classes=["result-card", "benchmark-card"]):
                    image = gr.Image(
                        label=f"Saved model output {index + 1}",
                        interactive=False, height=240,
                    )
                    metrics = gr.HTML()
                    cards.extend([image, metrics])

    outputs = [prompt_text, *cards]
    prompt_id.input(_display_prompt, inputs=prompt_id, outputs=outputs)
    dashboard.load(_display_prompt, inputs=prompt_id, outputs=outputs)
