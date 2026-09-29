"""Check frontend aspect-ratio sizes against the deployed image APIs."""

import ast
import base64
import binascii
from io import BytesIO
import os
from pathlib import Path
import sys
import time

from PIL import Image
import requests


PROMPT = "A red ceramic mug on a plain white background"
BACKENDS = (
    ("FLUX", "black-forest-labs/FLUX.2-klein-4B", "FLUX_ENDPOINT", "FLUX_TOKEN"),
    ("Z-Image Turbo", "Tongyi-MAI/Z-Image-Turbo", "ZIMAGE_ENDPOINT", "ZIMAGE_TOKEN"),
)


def frontend_sizes() -> dict[str, dict[str, str]]:
    """Read the literal UI mapping without importing Gradio or backend services."""
    source = Path(__file__).resolve().parents[1] / "app/components/generation.py"
    for node in ast.parse(source.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ASPECT_SIZES"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise ValueError(f"ASPECT_SIZES not found in {source}")


def validate(endpoint: str, token: str, model_id: str, size: str) -> tuple[str, str, str]:
    """Return actual size, elapsed time, and a safe failure reason (or empty reason)."""
    started = time.perf_counter()
    try:
        response = requests.post(
            endpoint,
            json={"model": model_id, "prompt": PROMPT, "size": size,
                  "response_format": "b64_json"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=300,
        )
        if response.status_code != 200:
            return "—", f"{time.perf_counter() - started:.2f} s", f"HTTP {response.status_code}"
        encoded = response.json()["data"][0]["b64_json"]
        with Image.open(BytesIO(base64.b64decode(encoded, validate=True))) as image:
            image.load()
            actual = f"{image.width}x{image.height}"
        reason = "" if actual == size else "Dimensions do not match"
    except requests.Timeout:
        actual, reason = "—", "Timeout"
    except requests.RequestException:
        actual, reason = "—", "Connection/request error"
    except (KeyError, IndexError, TypeError, ValueError, OSError, AttributeError, binascii.Error):
        actual, reason = "—", "Invalid image response"
    return actual, f"{time.perf_counter() - started:.2f} s", reason


def main() -> int:
    try:
        sizes = frontend_sizes()
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"Cannot read frontend aspect-ratio mapping: {exc}", file=sys.stderr)
        return 1

    print("Model | Aspect Ratio | Requested Size | Returned Size | Time | Pass/Fail")
    print("--- | --- | --- | --- | --- | ---")
    failures = []
    for name, model_id, endpoint_var, token_var in BACKENDS:
        endpoint, token = os.environ.get(endpoint_var), os.environ.get(token_var)
        for ratio, size in sizes[name].items():
            if not endpoint or not token:
                actual, elapsed = "—", "—"
                reason = "Missing " + ", ".join(
                    var for var, value in ((endpoint_var, endpoint), (token_var, token)) if not value
                )
            else:
                actual, elapsed, reason = validate(endpoint, token, model_id, size)
            passed = not reason
            print(f"{name} | {ratio} | {size} | {actual} | {elapsed} | {'Pass' if passed else 'Fail'}", flush=True)
            if not passed:
                failures.append(f"{name} / {ratio}: {reason}")

    for failure in failures:
        print(failure, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
