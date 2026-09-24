"""Lightweight, blind human-preference controls for displayed outputs."""

from dataclasses import dataclass

import gradio as gr


@dataclass
class EvaluationUI:
    """Components available for future preference persistence or analytics."""

    preference: gr.Radio
    submit_button: gr.Button
    confirmation: gr.Markdown


def _submit_preference(preference: str | None) -> str:
    """Validate input without storing anything in project datasets."""
    if preference is None:
        return "<span class='validation-message'>Select a direct preference before submitting.</span>"
    return "<span class='success-message'>Preference received for this session. It has not been saved to a dataset.</span>"


def build_evaluation_section() -> EvaluationUI:
    """Render a blind A/B preference control and a non-persistent action."""
    preference = gr.Radio(
        choices=["A", "B", "Tie"],
        label="Direct preference comparison",
        info="Choose the preferred available output (left is A, center is B), or select Tie.",
    )
    submit_button = gr.Button("Submit preference", variant="secondary")
    confirmation = gr.Markdown("<span class='status-note'>Preferences are validated in the UI only for now.</span>")
    submit_button.click(_submit_preference, inputs=preference, outputs=confirmation)
    return EvaluationUI(preference, submit_button, confirmation)
