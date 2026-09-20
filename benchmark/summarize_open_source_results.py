import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize Beamdata open-source benchmark results"
    )
    parser.add_argument(
        "--resolution",
        default="1024",
        help="Resolution folder to summarize, e.g. 512, 1024, or 1024x768",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    results_dir = Path("benchmark/results/baseline") / args.resolution
    input_file = results_dir / "benchmark_results.csv"
    output_file = results_dir / "benchmark_summary.csv"

    if not input_file.exists():
        raise FileNotFoundError(
            f"Benchmark results not found: {input_file}"
        )

    rows_by_provider = defaultdict(list)

    with open(input_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["run_type"] != "official":
                continue

            if str(row["success"]).lower() != "true":
                continue

            rows_by_provider[row["provider"]].append(row)

    summary_rows = []

    for provider, rows in rows_by_provider.items():
        latencies = [
            float(row["generation_time_seconds"])
            for row in rows
        ]

        vrams = [
            int(row["peak_vram_mib_observed"])
            for row in rows
            if row["peak_vram_mib_observed"]
        ]

        model = rows[0]["model"]
        total = len(rows)

        widths = {
            row["width"]
            for row in rows
            if row.get("width")
        }
        heights = {
            row["height"]
            for row in rows
            if row.get("height")
        }

        summary_rows.append({
            "provider": provider,
            "model": model,
            "resolution": (
                f"{next(iter(widths))}x{next(iter(heights))}"
                if len(widths) == 1 and len(heights) == 1
                else args.resolution
            ),
            "successful_generations": total,
            "average_latency_seconds": round(
                statistics.mean(latencies), 3
            ),
            "median_latency_seconds": round(
                statistics.median(latencies), 3
            ),
            "min_latency_seconds": round(min(latencies), 3),
            "max_latency_seconds": round(max(latencies), 3),
            "peak_vram_mib": max(vrams) if vrams else "",
            "peak_vram_gib": (
                round(max(vrams) / 1024, 2)
                if vrams
                else ""
            ),
        })

    fieldnames = [
        "provider",
        "model",
        "resolution",
        "successful_generations",
        "average_latency_seconds",
        "median_latency_seconds",
        "min_latency_seconds",
        "max_latency_seconds",
        "peak_vram_mib",
        "peak_vram_gib",
    ]

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    for row in summary_rows:
        print()
        print(row["provider"])
        print("Model:", row["model"])
        print("Resolution:", row["resolution"])
        print(
            "Successful generations:",
            row["successful_generations"],
        )
        print(
            "Average latency:",
            row["average_latency_seconds"],
            "s",
        )
        print(
            "Median latency:",
            row["median_latency_seconds"],
            "s",
        )
        print(
            "Min latency:",
            row["min_latency_seconds"],
            "s",
        )
        print(
            "Max latency:",
            row["max_latency_seconds"],
            "s",
        )
        print(
            "Peak VRAM:",
            row["peak_vram_gib"],
            "GiB",
        )

    print()
    print("Saved:", output_file)


if __name__ == "__main__":
    main()