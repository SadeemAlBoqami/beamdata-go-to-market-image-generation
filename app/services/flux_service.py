"""Client for the externally hosted FLUX vLLM-Omni image endpoint."""

import base64
from dataclasses import dataclass
from io import BytesIO
import os
import time

from PIL import Image
import requests


FLUX_ENDPOINT = os.environ.get(
    "FLUX_ENDPOINT", "http://127.0.0.1:8005/v1/images/generations"
)
FLUX_MODEL = "black-forest-labs/FLUX.2-klein-4B"
REQUEST_TIMEOUT_SECONDS = 300


@dataclass
class FluxGenerationResult:
    """A normalized response for the Gradio UI, whether generation succeeds or fails."""

    image: Image.Image | None
    generation_time: float
    peak_vram: None
    success: bool
    error: str | None


def generate_flux(prompt: str) -> FluxGenerationResult:
    """Request a FLUX image without loading a model in the Gradio process."""
    started_at = time.perf_counter()
    payload = {
        "model": FLUX_MODEL,
        "prompt": prompt,
        "size": "1024x1024",
        "response_format": "b64_json",
    }

    try:
        response = requests.post(FLUX_ENDPOINT, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code != 200:
            response_body = response.text.strip().replace("\n", " ")
            detail = f": {response_body[:300]}" if response_body else ""
            raise requests.HTTPError(f"FLUX endpoint returned HTTP {response.status_code}{detail}")

        encoded_image = response.json()["data"][0]["b64_json"]
        image = Image.open(BytesIO(base64.b64decode(encoded_image))).copy()
    except requests.RequestException as error:
        return FluxGenerationResult(
            image=None,
            generation_time=time.perf_counter() - started_at,
            peak_vram=None,
            success=False,
            error=f"FLUX request failed: {error}",
        )
    except (KeyError, IndexError, TypeError, ValueError, OSError) as error:
        return FluxGenerationResult(
            image=None,
            generation_time=time.perf_counter() - started_at,
            peak_vram=None,
            success=False,
            error=f"FLUX returned an invalid image response: {error}",
        )

    return FluxGenerationResult(
        image=image,
        generation_time=time.perf_counter() - started_at,
        peak_vram=None,
        success=True,
        error=None,
    )
