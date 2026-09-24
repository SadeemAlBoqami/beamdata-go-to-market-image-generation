"""Read saved benchmark artifacts for the comparison tab."""

import csv
import json
from pathlib import Path
import hashlib


REPO_ROOT = Path(__file__).resolve().parents[2]

PROMPTS_PATH = (
    REPO_ROOT
    / "benchmark"
    / "prompts"
    / "benchmark_prompts.json"
)

COMMERCIAL_RESULTS = (
    REPO_ROOT
    / "benchmark"
    / "results"
    / "benchmark_results.csv"
)

FLUX_RESULTS = (
    REPO_ROOT
    / "benchmark"
    / "results"
    / "open_source"
    / "flux2-klein"
    / "q4_k_m"
    / "512"
    / "results.csv"
)

ZIMAGE_RESULTS = (
    REPO_ROOT
    / "benchmark"
    / "results"
    / "open_source"
    / "z-image-turbo"
    / "w4"
    / "512"
    / "results.csv"
)


MODEL_SOURCES = [
    {
        "name": "GPT Image 2",
        "csv": COMMERCIAL_RESULTS,
        "model": "gpt-image-2",
    },
    {
        "name": "FLUX 2 Pro",
        "csv": COMMERCIAL_RESULTS,
        "model": "flux-2-pro",
    },
    {
        "name": "Gemini 3.1 Flash Image",
        "csv": COMMERCIAL_RESULTS,
        "model": "gemini-3.1-flash-image",
    },
    {
        "name": "FLUX.2 Klein 4B Q4_K_M",
        "csv": FLUX_RESULTS,
        "model": "black-forest-labs/FLUX.2-klein-4B",
    },
    {
        "name": "Z-Image-Turbo W4",
        "csv": ZIMAGE_RESULTS,
        "model": "Tongyi-MAI/Z-Image-Turbo",
    },
]


def load_prompt_choices() -> list[tuple[str, str]]:
    """List prompt IDs from the existing benchmark prompt set."""

    if not PROMPTS_PATH.is_file():
        return []

    with PROMPTS_PATH.open(encoding="utf-8") as source:
        prompts = json.load(source)

    return [
        (
            f"{item['prompt_id']} · "
            f"{item['category'].replace('_', ' ')}",
            item["prompt_id"],
        )
        for item in prompts
    ]

def _saved_image(csv_path: Path, recorded_path: str) -> str | None:
    """Resolve saved image paths, including older moved benchmark paths."""

    if not recorded_path:
        return None

    name = Path(recorded_path).name

    # Open-source benchmark images live beside their CSV.
    local = csv_path.parent / "images" / name

    if local.is_file():
        return str(local)

    # Commercial benchmark CSV already records the repository path.
    recorded = (REPO_ROOT / recorded_path).resolve()

    if (
        recorded.is_relative_to(REPO_ROOT)
        and recorded.is_file()
    ):
        return str(recorded)

    return None


def _find_row(
    csv_path: Path,
    prompt_id: str,
    model_id: str,
) -> dict | None:
    """Find the final successful benchmark row for one model/prompt."""

    with csv_path.open(
        newline="",
        encoding="utf-8",
    ) as source:

        rows = csv.DictReader(source)

        for row in rows:

            if row.get("prompt_id") != prompt_id:
                continue

            if row.get("model") != model_id:
                continue

            if row.get("success", "").lower() != "true":
                continue

            # Commercial benchmark contains the final-benchmark flag.
            final_flag = row.get("included_in_final_benchmark")

            if final_flag is not None:
                if final_flag.lower() != "true":
                    continue

            return row

    return None

def _blind_order(
    prompt_id: str,
    records: list[dict],
) -> list[dict]:
    """
    Return a deterministic blind order for the five models.

    The order changes between prompts but stays identical
    every time the same prompt is loaded.
    """

    return sorted(
        records,
        key=lambda record: hashlib.sha256(
            f"{prompt_id}|{record.get('model', '')}".encode("utf-8")
        ).hexdigest(),
    )

def load_comparison(
    prompt_id: str,
) -> tuple[str, list[dict]]:
    """Return prompt text and saved results for all five models."""

    with PROMPTS_PATH.open(encoding="utf-8") as source:
        prompt = next(
            (
                item["prompt"]
                for item in json.load(source)
                if item["prompt_id"] == prompt_id
            ),
            "",
        )

    records = []

    for source in MODEL_SOURCES:

        row = _find_row(
            source["csv"],
            prompt_id,
            source["model"],
        )

        if row is None:
            records.append(
                {
                    "image": None,
                    "model": source["name"],
                    "generation_time": "—",
                    "resolution": "—",
                    "success": False,
                    "cost": "—",
                }
            )
            continue

        image_path = _saved_image(
            source["csv"],
            row.get("image_path", ""),
        )

        width = row.get("width")
        height = row.get("height")

        records.append(
            {
                "image": image_path,
                "model": source["name"],
                "generation_time": (
                    row.get("generation_time_seconds") or "—"
                ),
                "resolution": (
                    f"{width} × {height}"
                    if width and height
                    else "—"
                ),
                "success": bool(image_path),
                "cost": (
                    row.get("estimated_cost_usd") or "—"
                ),
            }
        )

    records = _blind_order(
        prompt_id,
        records,
    )

    return prompt, records