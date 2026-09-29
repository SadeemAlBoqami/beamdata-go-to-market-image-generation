"""Entry point for the Image Generation Model Evaluation dashboard."""

from pathlib import Path

import gradio as gr

APP_DIR = Path(__file__).resolve().parent
CSS_PATH = APP_DIR / "assets" / "custom.css"

try:  # Supports both `python -m app.app` and `python app/app.py`.
    from .components.benchmark import build_benchmark_section
    from .components.generation import build_generation_section
    from .components.human_evaluation import build_human_evaluation_section
except ImportError:  # pragma: no cover - convenience for direct execution
    from components.benchmark import build_benchmark_section
    from components.generation import build_generation_section
    from components.human_evaluation import build_human_evaluation_section


def _load_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def build_dashboard() -> gr.Blocks:
    """Create the frontend and read saved benchmark data without rerunning it."""
    with gr.Blocks(
        title="Image Generation Model Evaluation",
    ) as dashboard:
        gr.HTML(
            "<header class='hero'><p class='eyebrow'>BEAMDATA · MODEL LAB</p>"
            "<h1>Image Generation Model Evaluation</h1>"
            "<p>Compare open-source image-generation models for marketing use cases, "
            "review outputs, and collect human evaluation feedback.</p></header>"
        )

        with gr.Tabs():
            with gr.Tab("Generate"):
                with gr.Group(elem_classes=["dashboard-section"]):
                    gr.HTML("<h2>Generate comparison</h2><p class='section-copy'>"
                            "Create images with the available deployed models.</p>")
                    build_generation_section()

            with gr.Tab("Benchmark Comparison"):
                with gr.Group(elem_classes=["dashboard-section"]):
                    gr.HTML("<h2>Saved benchmark comparison</h2><p class='section-copy'>"
                            "Review existing final-model benchmark images and metadata. "
                            "No benchmark is run on this page.</p>")
                    build_benchmark_section(dashboard)

            with gr.Tab("Human Evaluation"):
                with gr.Group(elem_classes=["dashboard-section"]):
                    gr.HTML("<h2>Human evaluation</h2><p class='section-copy'>"
                            "Compare two saved images at a time and record your preference.</p>")
                    build_human_evaluation_section(dashboard)

    return dashboard

if __name__ == "__main__":
    build_dashboard().launch(
        server_name="0.0.0.0",
        server_port=7860,
        root_path="/proxy/80",
        theme=gr.themes.Base(primary_hue="indigo", neutral_hue="slate"),
        css=_load_css(),
    )
