"""Entry point for the Image Generation Model Evaluation dashboard."""

from pathlib import Path

import gradio as gr

APP_DIR = Path(__file__).resolve().parent
CSS_PATH = APP_DIR / "assets" / "custom.css"

try:  # Supports both `python -m app.app` and `python app/app.py`.
    from .components.evaluation import build_evaluation_section
    from .components.generation import build_generation_section
except ImportError:  # pragma: no cover - convenience for direct execution
    from components.evaluation import build_evaluation_section
    from components.generation import build_generation_section


def _load_css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def load_benchmark_results_placeholder() -> dict:
    """Future boundary for reading existing benchmark CSV/JSON output.

    This dashboard must consume saved benchmark data when that integration is
    added; it must not trigger a benchmark run from the UI.
    """
    return {}


def build_dashboard() -> gr.Blocks:
    """Create the frontend without loading models or benchmark data."""
    with gr.Blocks(
        title="Image Generation Model Evaluation",
        theme=gr.themes.Base(primary_hue="indigo", neutral_hue="slate"),
        css=_load_css(),
    ) as dashboard:
        gr.HTML(
            "<header class='hero'><p class='eyebrow'>BEAMDATA · MODEL LAB</p>"
            "<h1>Image Generation Model Evaluation</h1>"
            "<p>Compare open-source image-generation models for marketing use cases, "
            "review outputs, and collect human evaluation feedback.</p></header>"
        )

        with gr.Group(elem_classes=["dashboard-section"]):
            gr.HTML("<h2>Generate comparison</h2><p class='section-copy'>Select the models "
                    "you want to prepare for comparison. Backend model integration is pending.</p>")
            build_generation_section()

        with gr.Group(elem_classes=["dashboard-section", "evaluation-section"]):
            gr.HTML("<h2>Human preference</h2><p class='section-copy'>Choose the preferred "
                    "output from this side-by-side comparison.</p>")
            build_evaluation_section()

    return dashboard


if __name__ == "__main__":
    build_dashboard().launch()
