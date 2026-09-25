"""Read saved benchmark artifacts for the comparison tab."""

import csv
import json
from pathlib import Path


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
) -> tuple[dict | None, bool]:
    """Select one official row, never an arbitrary retry or duplicate."""
    if not csv_path.is_file():
        return None, False

    with csv_path.open(newline="", encoding="utf-8") as source:
        candidates = []
        for row in csv.DictReader(source):
            if row.get("prompt_id") != prompt_id or row.get("model") != model_id:
                continue
            if "run_type" in row and row["run_type"].lower() != "official":
                continue
            final_flag = row.get("included_in_final_benchmark")
            if final_flag is not None and final_flag.lower() != "true":
                continue
            candidates.append(row)

    if len(candidates) != 1:
        return None, len(candidates) > 1
    return candidates[0], False


def load_comparison(
    prompt_id: str,
) -> tuple[str, list[dict]]:
    """Return prompt text and one saved official result per model."""

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

        row, ambiguous = _find_row(
            source["csv"],
            prompt_id,
            source["model"],
        )

        if row is None:
            records.append(
                {
                    "image": None,
                    "image_path": None,
                    "model": source["name"],
                    "provider": None,
                    "generation_time": None,
                    "resolution": None,
                    "success": False,
                    "cost": None,
                    "peak_vram": None,
                    "status": (
                        "Ambiguous official outputs" if ambiguous
                        else "Saved output unavailable"
                    ),
                }
            )
            continue

        image_path = _saved_image(
            source["csv"],
            row.get("image_path", ""),
        )

        width = row.get("width")
        height = row.get("height")

        saved_success = row.get("success", "").lower() == "true"
        records.append(
            {
                "image": image_path,
                "image_path": image_path,
                "model": source["name"],
                "provider": row.get("provider") or None,
                "generation_time": row.get("generation_time_seconds") or None,
                "resolution": f"{width} × {height}" if width and height else None,
                "success": saved_success and bool(image_path),
                "cost": row.get("estimated_cost_usd") or None,
                "peak_vram": (
                    row.get("peak_vram_mib_observed")
                    or row.get("peak_vram_mib")
                    or None
                ),
                "status": (
                    "Success" if saved_success and image_path
                    else "Saved image unavailable" if saved_success
                    else "Failed"
                ),
            }
        )

    return prompt, records
