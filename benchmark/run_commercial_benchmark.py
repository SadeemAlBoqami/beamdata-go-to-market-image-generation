import argparse
import base64
import csv
import io
import json
import os
import subprocess
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from openai import OpenAI
from PIL import Image

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent

if SCRIPT_DIR.name == "benchmark":
    BENCHMARK_DIR = SCRIPT_DIR
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR
    BENCHMARK_DIR = PROJECT_ROOT / "benchmark"

load_dotenv(PROJECT_ROOT / ".env")

PROMPTS_FILE = BENCHMARK_DIR / "prompts" / "benchmark_prompts.json"
RESULTS_DIR = BENCHMARK_DIR / "results"
IMAGES_DIR = RESULTS_DIR / "images"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_IMAGE_BASE_URL = os.getenv("OPENAI_IMAGE_BASE_URL") or None
OPENAI_MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2")
OPENAI_QUALITY = os.getenv("OPENAI_IMAGE_QUALITY", "medium")
OPENAI_SIZE = os.getenv("OPENAI_IMAGE_SIZE", "1024x1024")
OPENAI_COST_PER_IMAGE = float(os.getenv("OPENAI_COST_PER_IMAGE", "0.05"))

# BFL
BFL_API_KEY = os.getenv("BFL_API_KEY")
BFL_MODEL = os.getenv("BFL_IMAGE_MODEL", "flux-2-pro")
BFL_BASE_URL = os.getenv(
    "BFL_IMAGE_BASE_URL",
    f"https://api.bfl.ai/v1/{BFL_MODEL}",
)
BFL_WIDTH = int(os.getenv("BFL_IMAGE_WIDTH", "1024"))
BFL_HEIGHT = int(os.getenv("BFL_IMAGE_HEIGHT", "1024"))
BFL_TIMEOUT = int(os.getenv("BFL_TIMEOUT_SECONDS", "300"))
BFL_POLL_INTERVAL = float(os.getenv("BFL_POLL_INTERVAL_SECONDS", "2"))
BFL_COST_PER_MEGAPIXEL = float(os.getenv("BFL_COST_PER_MEGAPIXEL", "0.03"))

# Google
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GOOGLE_IMAGE_BASE_URL = os.getenv("GOOGLE_IMAGE_BASE_URL") or None
GEMINI_MODEL = os.getenv("GOOGLE_IMAGE_MODEL", "gemini-3.1-flash-image")
GEMINI_ASPECT_RATIO = os.getenv("GOOGLE_IMAGE_ASPECT_RATIO", "1:1")
GEMINI_IMAGE_SIZE = os.getenv("GOOGLE_IMAGE_SIZE", "1K")
GEMINI_COST_PER_IMAGE = float(os.getenv("GEMINI_COST_PER_IMAGE", "0.067"))

# GitHub
GITHUB_REPO_URL = os.getenv("GITHUB_REPO_URL", "").rstrip("/")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "")


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def ensure_directories():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def load_prompts():
    with open(PROMPTS_FILE, "r", encoding="utf-8") as file:
        prompts = json.load(file)

    if not isinstance(prompts, list):
        raise ValueError("benchmark_prompts.json must contain a JSON list")

    return prompts


def validate_prompts(prompts):
    seen_ids = set()

    for item in prompts:
        for key in ("prompt_id", "category", "prompt"):
            if key not in item:
                raise ValueError(f"Prompt missing '{key}': {item}")

        prompt_id = item["prompt_id"]
        if prompt_id in seen_ids:
            raise ValueError(f"Duplicate prompt_id: {prompt_id}")

        seen_ids.add(prompt_id)


def validate_official_set(prompts):
    if len(prompts) != 25:
        raise ValueError(f"Expected 25 prompts, found {len(prompts)}")

    counts = {}
    for item in prompts:
        category = item["category"]
        counts[category] = counts.get(category, 0) + 1

    if len(counts) != 5 or any(count != 5 for count in counts.values()):
        raise ValueError(f"Expected 5 prompts per category, found {counts}")


def image_size_bytes(path):
    path = Path(path)
    return path.stat().st_size if path.exists() else ""


def get_dimensions(path):
    with Image.open(path) as image:
        return image.size


def save_bytes_as_png(image_bytes, output_path):
    with Image.open(io.BytesIO(image_bytes)) as image:
        image.save(output_path, format="PNG")


def estimate_bfl_cost(width, height):
    megapixels = (width * height) / 1_000_000
    return round(BFL_COST_PER_MEGAPIXEL * megapixels, 6)


def git_value(*args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), *args],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def detect_github_repo_url():
    if GITHUB_REPO_URL:
        return GITHUB_REPO_URL

    remote = git_value("remote", "get-url", "origin")
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.split(":", 1)[1]
    elif remote.startswith("ssh://git@github.com/"):
        remote = "https://github.com/" + remote.split("github.com/", 1)[1]

    if remote.startswith("https://github.com/"):
        return remote.removesuffix(".git").rstrip("/")

    return ""


def detect_git_branch():
    if GITHUB_BRANCH:
        return GITHUB_BRANCH

    branch = git_value("branch", "--show-current")
    return branch or "main"


def repo_relative_path(path):
    return Path(path).resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()


def build_image_url(image_path):
    repo_url = detect_github_repo_url()
    if not repo_url:
        return ""

    repo_path = repo_url.replace("https://github.com/", "", 1).strip("/")
    branch = quote(detect_git_branch(), safe="")
    rel_path = quote(repo_relative_path(image_path), safe="/")

    return (
        f"https://raw.githubusercontent.com/"
        f"{repo_path}/{branch}/{rel_path}"
    )


def make_output_path(run_id, prompt_id, provider):
    provider_dir = IMAGES_DIR / provider
    provider_dir.mkdir(parents=True, exist_ok=True)

    short_run = run_id.split("-")[0]
    return provider_dir / f"{short_run}_{prompt_id}.png"


CSV_FIELDS = [
    "run_id",
    "run_type",
    "included_in_final_benchmark",
    "prompt_id",
    "prompt",
    "category",
    "provider",
    "model",
    "width",
    "height",
    "generation_time_seconds",
    "estimated_cost_usd",
    "success",
    "error",
    "image_url",
    "timestamp",
    "difficulty",
    "provider_request_id",
    "image_path",
    "image_size_bytes",
    "retry_count",
    "attempt_number",
]


def append_csv(row, csv_file):
    exists = csv_file.exists()

    with open(csv_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)

        if not exists:
            writer.writeheader()

        writer.writerow(row)


def generate_openai(prompt_item, run_id):
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_IMAGE_BASE_URL,
    )

    start = time.perf_counter()

    result = client.images.generate(
        model=OPENAI_MODEL,
        prompt=prompt_item["prompt"],
        size=OPENAI_SIZE,
        quality=OPENAI_QUALITY,
    )

    elapsed = time.perf_counter() - start

    image_bytes = base64.b64decode(result.data[0].b64_json)
    output_path = make_output_path(run_id, prompt_item["prompt_id"], "openai")
    save_bytes_as_png(image_bytes, output_path)

    width, height = get_dimensions(output_path)

    return {
        "generation_time_seconds": round(elapsed, 3),
        "image_path": output_path,
        "provider_request_id": getattr(result, "id", "") or "",
        "estimated_cost_usd": OPENAI_COST_PER_IMAGE,
        "width": width,
        "height": height,
    }


def generate_bfl(prompt_item, run_id):
    headers = {
        "accept": "application/json",
        "x-key": BFL_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt_item["prompt"],
        "width": BFL_WIDTH,
        "height": BFL_HEIGHT,
    }

    start = time.perf_counter()

    response = requests.post(
        BFL_BASE_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    request_id = data.get("id", "")
    polling_url = data.get("polling_url")

    if not polling_url:
        raise RuntimeError("BFL response missing polling_url")

    deadline = time.time() + BFL_TIMEOUT

    while True:
        if time.time() > deadline:
            raise TimeoutError("BFL generation timed out")

        time.sleep(BFL_POLL_INTERVAL)

        poll_response = requests.get(
            polling_url,
            headers={"accept": "application/json", "x-key": BFL_API_KEY},
            timeout=60,
        )
        poll_response.raise_for_status()

        poll_data = poll_response.json()
        status = poll_data.get("status")

        if status == "Ready":
            image_url = poll_data.get("result", {}).get("sample")
            if not image_url:
                raise RuntimeError("BFL Ready response missing image URL")
            break

        if status in ("Error", "Failed"):
            raise RuntimeError(f"BFL generation failed: {poll_data}")

    image_response = requests.get(image_url, timeout=60)
    image_response.raise_for_status()

    elapsed = time.perf_counter() - start

    output_path = make_output_path(run_id, prompt_item["prompt_id"], "bfl")
    save_bytes_as_png(image_response.content, output_path)

    width, height = get_dimensions(output_path)

    return {
        "generation_time_seconds": round(elapsed, 3),
        "image_path": output_path,
        "provider_request_id": request_id,
        "estimated_cost_usd": estimate_bfl_cost(width, height),
        "width": width,
        "height": height,
    }


def generate_gemini(prompt_item, run_id):
    client_kwargs = {"api_key": GOOGLE_API_KEY}

    if GOOGLE_IMAGE_BASE_URL:
        client_kwargs["http_options"] = types.HttpOptions(
            base_url=GOOGLE_IMAGE_BASE_URL
        )

    client = genai.Client(**client_kwargs)

    start = time.perf_counter()

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[prompt_item["prompt"]],
        config=types.GenerateContentConfig(
            response_modalities=["Image"],
            image_config=types.ImageConfig(
                aspect_ratio=GEMINI_ASPECT_RATIO,
                image_size=GEMINI_IMAGE_SIZE,
            ),
        ),
    )

    elapsed = time.perf_counter() - start
    image = None

    candidates = getattr(response, "candidates", None) or []

    for candidate in candidates:
        parts = getattr(candidate.content, "parts", None) or []

        for part in parts:
            if getattr(part, "inline_data", None) is not None:
                image = part.as_image()
                break

        if image is not None:
            break

    if image is None:
        raise RuntimeError("Gemini response missing image")

    output_path = make_output_path(run_id, prompt_item["prompt_id"], "google")
    image.save(output_path)

    width, height = get_dimensions(output_path)

    return {
        "generation_time_seconds": round(elapsed, 3),
        "image_path": output_path,
        "provider_request_id": "",
        "estimated_cost_usd": GEMINI_COST_PER_IMAGE,
        "width": width,
        "height": height,
    }


def generate(provider, prompt_item, run_id):
    if provider == "openai":
        return generate_openai(prompt_item, run_id)

    if provider == "bfl":
        return generate_bfl(prompt_item, run_id)

    if provider == "google":
        return generate_gemini(prompt_item, run_id)

    raise ValueError(f"Unknown provider: {provider}")


def model_name(provider):
    if provider == "openai":
        return OPENAI_MODEL

    if provider == "bfl":
        return BFL_MODEL

    if provider == "google":
        return GEMINI_MODEL

    return ""


def provider_key_present(provider):
    if provider == "openai":
        return bool(OPENAI_API_KEY)

    if provider == "bfl":
        return bool(BFL_API_KEY)

    if provider == "google":
        return bool(GOOGLE_API_KEY)

    return False


def run_benchmark(providers, prompt_ids=None, max_retries=0, require_25=False):
    ensure_directories()

    run_type = "official" if require_25 else "smoke_test"
    csv_file = RESULTS_DIR / (
        "benchmark_results.csv"
        if require_25
        else "smoke_test_results.csv"
    )

    prompts = load_prompts()
    validate_prompts(prompts)

    if require_25:
        validate_official_set(prompts)

    if prompt_ids:
        requested = set(prompt_ids)
        prompts = [p for p in prompts if p["prompt_id"] in requested]

        found = {p["prompt_id"] for p in prompts}
        missing = requested - found

        if missing:
            raise ValueError(f"Prompt IDs not found: {sorted(missing)}")

    run_id = str(uuid.uuid4())

    print(f"\nRun ID: {run_id}")
    print(f"Prompts: {len(prompts)}")
    print(f"Providers: {providers}")
    print(f"Run type: {run_type}")
    print(f"CSV: {repo_relative_path(csv_file)}\n")

    repo_url = detect_github_repo_url()
    if repo_url:
        print(f"GitHub: {repo_url}")
        print(f"Branch: {detect_git_branch()}\n")
    else:
        print("GitHub URL not detected. image_url will be empty.\n")

    for prompt_item in prompts:
        for provider in providers:
            if not provider_key_present(provider):
                print(f"Skipping {provider}: API key missing")
                continue

            for attempt in range(1, max_retries + 2):
                print(
                    f"{prompt_item['prompt_id']} | "
                    f"{provider} | attempt {attempt}"
                )

                success = False
                error = ""
                generation_time = ""
                image_path = ""
                provider_request_id = ""
                cost = ""
                width = ""
                height = ""

                attempt_start = time.perf_counter()

                try:
                    result = generate(provider, prompt_item, run_id)

                    success = True
                    generation_time = result["generation_time_seconds"]
                    image_path = result["image_path"]
                    provider_request_id = result.get(
                        "provider_request_id", ""
                    )
                    cost = result.get("estimated_cost_usd", "")
                    width = result.get("width", "")
                    height = result.get("height", "")

                except Exception as exc:
                    error = str(exc)
                    generation_time = round(
                        time.perf_counter() - attempt_start,
                        3,
                    )

                image_path_csv = (
                    repo_relative_path(image_path)
                    if image_path
                    else ""
                )

                row = {
                    "run_id": run_id,
                    "run_type": run_type,
                    "included_in_final_benchmark": require_25,
                    "prompt_id": prompt_item["prompt_id"],
                    "prompt": prompt_item["prompt"],
                    "category": prompt_item["category"],
                    "provider": provider,
                    "model": model_name(provider),
                    "width": width,
                    "height": height,
                    "generation_time_seconds": generation_time,
                    "estimated_cost_usd": cost,
                    "success": success,
                    "error": error,
                    "image_url": (
                        build_image_url(image_path)
                        if image_path
                        else ""
                    ),
                    "timestamp": utc_timestamp(),
                    "difficulty": prompt_item.get("difficulty", ""),
                    "provider_request_id": provider_request_id,
                    "image_path": image_path_csv,
                    "image_size_bytes": (
                        image_size_bytes(image_path)
                        if image_path
                        else ""
                    ),
                    "retry_count": attempt - 1,
                    "attempt_number": attempt,
                }

                append_csv(row, csv_file)

                if success:
                    print(
                        f"  SUCCESS ({generation_time}s) "
                        f"-> {image_path_csv}"
                    )
                    print(f"  URL: {row['image_url']}")
                    break

                print(f"  FAILED: {error}")

                if attempt <= max_retries:
                    print("  Retrying...")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Beamdata commercial image benchmark"
    )

    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["openai", "bfl", "google"],
        default=["openai", "bfl", "google"],
        help="Providers to run",
    )

    parser.add_argument(
        "--prompt-ids",
        nargs="+",
        default=["PL-01"],
        help="Prompt IDs for a smoke test",
    )

    parser.add_argument(
        "--all-prompts",
        action="store_true",
        help="Run all 25 prompts",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=0,
        help="Retries after failure",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.all_prompts:
        run_benchmark(
            providers=args.providers,
            prompt_ids=None,
            max_retries=args.max_retries,
            require_25=True,
        )
    else:
        run_benchmark(
            providers=args.providers,
            prompt_ids=args.prompt_ids,
            max_retries=args.max_retries,
            require_25=False,
        )
