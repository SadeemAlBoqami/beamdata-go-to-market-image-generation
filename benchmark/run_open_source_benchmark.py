import argparse
import base64
import csv
import json
import os
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

PROMPTS_FILE = SCRIPT_DIR / "prompts" / "benchmark_prompts.json"
RESULTS_DIR = SCRIPT_DIR / "results"

DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
SEED = 42
VRAM_SAMPLE_INTERVAL_SECONDS = 0.1


PROVIDERS = {
    "flux-klein": {
        "base_url": os.getenv(
            "FLUX_KLEIN_BASE_URL",
            "http://localhost:8000",
        ),
        "model": os.getenv(
            "FLUX_KLEIN_MODEL",
            "black-forest-labs/FLUX.2-klein-4B",
        ),
    },
    "sd35-medium": {
        "base_url": os.getenv(
            "SD35_MEDIUM_BASE_URL",
            "http://localhost:8001",
        ),
        "model": os.getenv(
            "SD35_MEDIUM_MODEL",
            "stabilityai/stable-diffusion-3.5-medium",
        ),
    },
        "sdxl-base": {
        "base_url": os.getenv(
            "SDXL_BASE_URL",
            "http://localhost:8001",
        ),
        "model": os.getenv(
            "SDXL_MODEL",
            "/models/sdxl-fp16",
        ),
    },
        "z-image-turbo": {
        "base_url": os.getenv(
            "Z_IMAGE_TURBO_BASE_URL",
            "http://localhost:8003",
        ),
        "model": os.getenv(
            "Z_IMAGE_TURBO_MODEL",
            "/models/z-image-turbo",
        ),
    },
}


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def load_prompts():
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        prompts = json.load(f)

    if not isinstance(prompts, list):
        raise ValueError("benchmark_prompts.json must contain a list")

    return prompts


def validate_official_set(prompts):
    if len(prompts) != 25:
        raise ValueError(f"Expected 25 prompts, found {len(prompts)}")


def get_run_paths(width, height):
    resolution_name = (
        str(width)
        if width == height
        else f"{width}x{height}"
    )

    run_results_dir = RESULTS_DIR / "baseline" / resolution_name
    run_images_dir = run_results_dir / "images"

    run_results_dir.mkdir(parents=True, exist_ok=True)

    for provider in PROVIDERS:
        (run_images_dir / provider).mkdir(parents=True, exist_ok=True)

    return run_results_dir, run_images_dir


def image_size_bytes(path):
    return Path(path).stat().st_size


def get_gpu_name():
    try:
        return subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name",
                "--format=csv,noheader",
            ],
            text=True,
        ).strip()
    except Exception:
        return ""


def get_gpu_memory_used_mib():
    try:
        value = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()

        return int(value.splitlines()[0])
    except Exception:
        return None


def monitor_peak_vram(stop_event, samples, interval_seconds):
    """Sample total GPU memory usage until stop_event is set."""
    while not stop_event.is_set():
        value = get_gpu_memory_used_mib()
        if value is not None:
            samples.append(value)
        stop_event.wait(interval_seconds)

    # Final sample after the request finishes.
    value = get_gpu_memory_used_mib()
    if value is not None:
        samples.append(value)


def generate_image(
    provider,
    prompt_item,
    run_id,
    width,
    height,
    images_dir,
    vram_sample_interval_seconds,
):
    config = PROVIDERS[provider]

    payload = {
        "model": config["model"],
        "prompt": prompt_item["prompt"],
        "size": f"{width}x{height}",
        "response_format": "b64_json",
        "seed": SEED,
    }

    vram_samples = []
    stop_event = threading.Event()
    monitor_thread = threading.Thread(
        target=monitor_peak_vram,
        args=(
            stop_event,
            vram_samples,
            vram_sample_interval_seconds,
        ),
        daemon=True,
    )

    # Capture an initial sample before the request starts.
    initial_vram = get_gpu_memory_used_mib()
    if initial_vram is not None:
        vram_samples.append(initial_vram)

    monitor_thread.start()
    start = time.perf_counter()

    try:
        response = requests.post(
            f"{config['base_url']}/v1/images/generations",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=300,
        )
        elapsed = time.perf_counter() - start
        response.raise_for_status()

        data = response.json()
        image_b64 = data["data"][0]["b64_json"]
        image_bytes = base64.b64decode(image_b64)

        short_run = run_id.split("-")[0]
        output_path = (
            images_dir
            / provider
            / f"{short_run}_{prompt_item['prompt_id']}.png"
        )

        with open(output_path, "wb") as f:
            f.write(image_bytes)

    finally:
        stop_event.set()
        monitor_thread.join(timeout=2)

    peak_vram = max(vram_samples) if vram_samples else ""

    return {
        "generation_time_seconds": round(elapsed, 3),
        "image_path": output_path,
        "peak_vram_mib_observed": peak_vram,
    }


CSV_FIELDS = [
    "run_id",
    "run_type",
    "prompt_id",
    "prompt",
    "category",
    "provider",
    "model",
    "width",
    "height",
    "generation_time_seconds",
    "peak_vram_mib_observed",
    "gpu_used",
    "success",
    "error",
    "image_path",
    "image_size_bytes",
    "timestamp",
    "seed",
]


def append_csv(row, path):
    exists = path.exists()

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)

        if not exists:
            writer.writeheader()

        writer.writerow(row)


def run_benchmark(
    providers,
    prompt_ids=None,
    all_prompts=False,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
    vram_sample_interval_seconds=VRAM_SAMPLE_INTERVAL_SECONDS,
):
    run_results_dir, run_images_dir = get_run_paths(width, height)

    prompts = load_prompts()

    if all_prompts:
        validate_official_set(prompts)
        run_type = "official"
    else:
        run_type = "smoke_test"

    if prompt_ids:
        requested = set(prompt_ids)
        prompts = [p for p in prompts if p["prompt_id"] in requested]

        found = {p["prompt_id"] for p in prompts}
        missing = requested - found

        if missing:
            raise ValueError(f"Prompt IDs not found: {sorted(missing)}")

    run_id = str(uuid.uuid4())

    csv_file = run_results_dir / (
        "benchmark_results.csv"
        if all_prompts
        else "smoke_test_results.csv"
    )

    gpu_name = get_gpu_name()

    print(f"\nRun ID: {run_id}")
    print(f"Prompts: {len(prompts)}")
    print(f"Providers: {providers}")
    print(f"Resolution: {width}x{height}")
    print(f"GPU: {gpu_name}")
    print(f"Run type: {run_type}")
    print(f"VRAM sample interval: {vram_sample_interval_seconds:.3f}s")
    print(f"CSV: {csv_file}\n")

    for prompt_item in prompts:
        for provider in providers:
            config = PROVIDERS[provider]

            print(f"{prompt_item['prompt_id']} | {provider}")
            print(f"  Model: {config['model']}")
            print(f"  Endpoint: {config['base_url']}")

            success = False
            error = ""
            result = {}
            attempt_start = time.perf_counter()

            try:
                result = generate_image(
                    provider=provider,
                    prompt_item=prompt_item,
                    run_id=run_id,
                    width=width,
                    height=height,
                    images_dir=run_images_dir,
                    vram_sample_interval_seconds=vram_sample_interval_seconds,
                )
                success = True

                print(
                    "  SUCCESS "
                    f"({result['generation_time_seconds']}s, "
                    f"peak VRAM {result['peak_vram_mib_observed']} MiB)"
                )

            except Exception as exc:
                error = str(exc)
                result["generation_time_seconds"] = round(
                    time.perf_counter() - attempt_start,
                    3,
                )
                result["peak_vram_mib_observed"] = ""
                print(f"  FAILED: {error}")

            image_path = result.get("image_path", "")

            row = {
                "run_id": run_id,
                "run_type": run_type,
                "prompt_id": prompt_item["prompt_id"],
                "prompt": prompt_item["prompt"],
                "category": prompt_item["category"],
                "provider": provider,
                "model": config["model"],
                "width": width,
                "height": height,
                "generation_time_seconds": result.get(
                    "generation_time_seconds", ""
                ),
                "peak_vram_mib_observed": result.get(
                    "peak_vram_mib_observed", ""
                ),
                "gpu_used": gpu_name,
                "success": success,
                "error": error,
                "image_path": (
                    image_path.relative_to(PROJECT_ROOT).as_posix()
                    if image_path
                    else ""
                ),
                "image_size_bytes": (
                    image_size_bytes(image_path) if image_path else ""
                ),
                "timestamp": utc_timestamp(),
                "seed": SEED,
            }

            append_csv(row, csv_file)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Beamdata open-source image benchmark"
    )

    parser.add_argument(
        "--providers",
        nargs="+",
        choices=list(PROVIDERS.keys()),
        default=["flux-klein"],
    )

    parser.add_argument(
        "--prompt-ids",
        nargs="+",
        default=["PL-01"],
    )

    parser.add_argument(
        "--all-prompts",
        action="store_true",
    )

    parser.add_argument(
        "--width",
        type=int,
        default=DEFAULT_WIDTH,
    )

    parser.add_argument(
        "--height",
        type=int,
        default=DEFAULT_HEIGHT,
    )

    parser.add_argument(
        "--vram-sample-ms",
        type=int,
        default=int(VRAM_SAMPLE_INTERVAL_SECONDS * 1000),
        help="VRAM sampling interval in milliseconds (default: 100)",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.width <= 0 or args.height <= 0:
        raise ValueError("width and height must be positive integers")

    if args.vram_sample_ms <= 0:
        raise ValueError("--vram-sample-ms must be > 0")

    run_benchmark(
        providers=args.providers,
        prompt_ids=None if args.all_prompts else args.prompt_ids,
        all_prompts=args.all_prompts,
        width=args.width,
        height=args.height,
        vram_sample_interval_seconds=args.vram_sample_ms / 1000,
    )