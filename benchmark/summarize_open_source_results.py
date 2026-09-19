import csv
import statistics
from collections import defaultdict
from pathlib import Path

INPUT = Path("benchmark/results/open_source_benchmark_results.csv")
OUTPUT = Path("benchmark/results/open_source_benchmark_summary.csv")

rows_by_provider = defaultdict(list)

with open(INPUT, encoding="utf-8") as f:
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

    summary_rows.append({
        "provider": provider,
        "model": model,
        "successful_generations": total,
        "average_latency_seconds": round(statistics.mean(latencies), 3),
        "median_latency_seconds": round(statistics.median(latencies), 3),
        "min_latency_seconds": round(min(latencies), 3),
        "max_latency_seconds": round(max(latencies), 3),
        "peak_vram_mib": max(vrams) if vrams else "",
        "peak_vram_gib": round(max(vrams) / 1024, 2) if vrams else "",
    })

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "provider",
            "model",
            "successful_generations",
            "average_latency_seconds",
            "median_latency_seconds",
            "min_latency_seconds",
            "max_latency_seconds",
            "peak_vram_mib",
            "peak_vram_gib",
        ],
    )

    writer.writeheader()
    writer.writerows(summary_rows)

for row in summary_rows:
    print()
    print(row["provider"])
    print("Model:", row["model"])
    print("Successful generations:", row["successful_generations"])
    print("Average latency:", row["average_latency_seconds"], "s")
    print("Median latency:", row["median_latency_seconds"], "s")
    print("Min latency:", row["min_latency_seconds"], "s")
    print("Max latency:", row["max_latency_seconds"], "s")
    print("Peak VRAM:", row["peak_vram_gib"], "GiB")

print()
print("Saved:", OUTPUT)
