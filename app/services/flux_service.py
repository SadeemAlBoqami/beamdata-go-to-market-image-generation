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
FLUX_TOKEN = os.environ.get("FLUX_TOKEN")
FLUX_MODEL = "black-forest-labs/FLUX.2-klein-4B"
REQUEST_TIMEOUT_SECONDS = 300


@dataclass
class FluxGenerationResult:
    """A normalized response for the Gradio UI, whether generation succeeds or fails."""

    image: Image.Image | None
    generation_time: float
    peak_vram: float | None
    success: bool
    error: str | None


def generate_flux(prompt: str, size: str = "1024x1024") -> FluxGenerationResult:
    """Request a FLUX image without loading a model in the Gradio process."""
    started_at = time.perf_counter()
    payload = {
        "model": FLUX_MODEL,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
    }

    try:
        headers = {"Authorization": f"Bearer {FLUX_TOKEN}"} if FLUX_TOKEN else None
        response = requests.post(
            FLUX_ENDPOINT, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )
        if response.status_code != 200:
            if response.status_code in (401, 403):
                raise requests.HTTPError("Authentication failed. Check FLUX_TOKEN.")
            raise requests.HTTPError(f"Backend returned HTTP {response.status_code}.")

        body = response.json()

        encoded_image = body["data"][0]["b64_json"]
        image = Image.open(BytesIO(base64.b64decode(encoded_image))).copy()

        metrics = body.get("metrics") or {}
        peak_vram = metrics.get("peak_memory_mb")
        peak_vram = float(peak_vram) if peak_vram is not None else None
    except requests.Timeout:
        error_message = "The FLUX backend timed out. Please try again."
    except requests.ConnectionError:
        error_message = "The FLUX backend is unavailable. Check its endpoint."
    except requests.RequestException as error:
        error_message = str(error) if isinstance(error, requests.HTTPError) else "FLUX request failed."
    except (KeyError, IndexError, TypeError, ValueError, OSError):
        error_message = "FLUX returned an invalid image response."
    else:
        return FluxGenerationResult(
            image,
            time.perf_counter() - started_at,
            peak_vram,
            True,
            None
        )
    return FluxGenerationResult(None, time.perf_counter() - started_at, None, False, error_message)
