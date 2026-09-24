"""Read saved final-model benchmark artifacts for the comparison tab."""

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_PATH = REPO_ROOT / "benchmark" / "prompts" / "benchmark_prompts.json"
RESULT_FILES = (
    REPO_ROOT / "benchmark" / "results" / "open_source" / "flux2-klein" / "q4_k_m" / "512" / "results.csv",
    REPO_ROOT / "benchmark" / "results" / "open_source" / "z-image-turbo" / "w4" / "512" / "results.csv",
)


def load_prompt_choices() -> list[tuple[str, str]]:
    """List prompt IDs from the existing benchmark prompt set."""
    if not PROMPTS_PATH.is_file():
        return []
    with PROMPTS_PATH.open(encoding="utf-8") as source:
        prompts = json.load(source)
    return [
        (f"{item['prompt_id']} · {item['category'].replace('_', ' ')}", item["prompt_id"])
        for item in prompts
    ]


def _saved_image(csv_path: Path, recorded_path: str) -> str | None:
    """Prefer the image beside its CSV; older CSV paths point to moved folders."""
    name = Path(recorded_path).name
    local = csv_path.parent / "images" / name
    if local.is_file():
        return str(local)
    recorded = (REPO_ROOT / recorded_path).resolve()
    if recorded.is_relative_to(REPO_ROOT) and recorded.is_file():
        return str(recorded)
    return None


def load_comparison(prompt_id: str) -> tuple[str, list[dict]]:
    """Return prompt text and saved records for FLUX and Z-Image Turbo."""
    with PROMPTS_PATH.open(encoding="utf-8") as source:
        prompt = next(
            (item["prompt"] for item in json.load(source) if item["prompt_id"] == prompt_id),
            "",
        )
    records = []
    for csv_path in RESULT_FILES:
        with csv_path.open(newline="", encoding="utf-8") as source:
            row = next((item for item in csv.DictReader(source) if item["prompt_id"] == prompt_id), None)
        if row is None:
            records.append({})
            continue
        image_path = _saved_image(csv_path, row.get("image_path", ""))
        records.append({
            "image": image_path,
            "model": row.get("model", "—"),
            "generation_time": row.get("generation_time_seconds") or "—",
            "resolution": (
                f"{row['width']} × {row['height']}"
                if row.get("width") and row.get("height") else "—"
            ),
            "success": row.get("success", "").lower() == "true" and bool(image_path),
            "cost": row.get("estimated_cost_usd") or "—",
        })
    return prompt, records
