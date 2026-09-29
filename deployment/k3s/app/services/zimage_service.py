"""HTTP client for the separately deployed Z-Image Turbo vLLM-Omni backend."""

import base64
import binascii
from dataclasses import dataclass
from io import BytesIO
import os
import time

from PIL import Image
import requests


ZIMAGE_MODEL = "Tongyi-MAI/Z-Image-Turbo"
REQUEST_TIMEOUT_SECONDS = 300


@dataclass
class ZImageGenerationResult:
    image: Image.Image | None
    generation_time: float
    peak_vram: float | None
    success: bool
    error: str | None


def generate_zimage(prompt: str, size: str = "512x512") -> ZImageGenerationResult:
    """Generate through an existing endpoint; never load the model in Gradio."""
    started_at = time.perf_counter()
    endpoint = os.environ.get("ZIMAGE_ENDPOINT")
    token = os.environ.get("ZIMAGE_TOKEN")
    if not endpoint:
        return ZImageGenerationResult(
            None, 0.0, None, False, "Set ZIMAGE_ENDPOINT to the deployed image API URL."
        )

    headers = {"Authorization": f"Bearer {token}"} if token else None
    payload = {
        "model": ZIMAGE_MODEL,
        "prompt": prompt,
        "size": size,
        "response_format": "b64_json",
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        if response.status_code in (401, 403):
            raise requests.HTTPError("Authentication failed. Check ZIMAGE_TOKEN.")
        if response.status_code != 200:
            raise requests.HTTPError(f"Backend returned HTTP {response.status_code}.")

        body = response.json()
        image = Image.open(BytesIO(base64.b64decode(body["data"][0]["b64_json"], validate=True))).copy()
        metrics = body.get("metrics") or {}
        peak_vram = metrics.get("peak_memory_mb")
        peak_vram = float(peak_vram) if peak_vram is not None else None
    except requests.Timeout:
        error_message = "The Z-Image backend timed out. Please try again."
    except requests.ConnectionError:
        error_message = "The Z-Image backend is unavailable. Check its endpoint."
    except requests.RequestException as error:
        error_message = str(error) if isinstance(error, requests.HTTPError) else "Z-Image request failed."
    except (KeyError, IndexError, TypeError, ValueError, OSError, AttributeError, binascii.Error):
        error_message = "Z-Image returned an invalid image response."
    else:
        return ZImageGenerationResult(image, time.perf_counter() - started_at, peak_vram, True, None)
    return ZImageGenerationResult(None, time.perf_counter() - started_at, None, False, error_message)
