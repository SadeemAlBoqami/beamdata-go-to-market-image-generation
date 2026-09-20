import csv
import json
import subprocess
import threading
import time
from pathlib import Path

import torch
from diffusers import QwenImage21Pipeline

PROMPT_IDS = ["PL-01", "PL-02", "PL-03", "PL-04", "PL-05"]
PROMPTS_FILE = Path("/workspace/benchmark/prompts/benchmark_prompts.json")
OUTPUT_DIR = Path("/workspace/qwen-image-2.1/results/1024")
CSV_PATH = OUTPUT_DIR / "pl01_pl05_results_1024.csv"

MODEL_PATH = "/models/qwen-image-2.1"
WIDTH = 1024
HEIGHT = 1024
SAMPLE_INTERVAL = 0.2

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_gpu_memory_mib():
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip()
        return int(out.splitlines()[0])
    except Exception:
        return -1

class VramMonitor:
    def __init__(self, interval=0.2):
        self.interval = interval
        self.peak_mib = 0
        self._stop = False
        self._thread = None

    def _run(self):
        while not self._stop:
            v = get_gpu_memory_mib()
            if v > self.peak_mib:
                self.peak_mib = v
            time.sleep(self.interval)

    def start(self):
        self._stop = False
        self.peak_mib = get_gpu_memory_mib()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop = True
        if self._thread is not None:
            self._thread.join(timeout=2)

with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

prompt_map = {item["prompt_id"]: item["prompt"] for item in data}
selected = [(pid, prompt_map[pid]) for pid in PROMPT_IDS]

print("Loading QwenImage21Pipeline from:", MODEL_PATH)
pipe = QwenImage21Pipeline.from_pretrained(
    MODEL_PATH,
    torch_dtype=torch.bfloat16,
)
pipe.enable_model_cpu_offload()

rows = []

for prompt_id, prompt in selected:
    print(f"\n=== {prompt_id} ===")
    print(prompt)

    image_path = OUTPUT_DIR / f"{prompt_id}.png"

    success = False
    error_message = ""
    latency = ""
    peak_vram_mib = ""

    try:
        torch.cuda.empty_cache()
        if torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()

        monitor = VramMonitor(interval=SAMPLE_INTERVAL)
        monitor.start()

        start = time.time()
        result = pipe(
            prompt=prompt,
            width=WIDTH,
            height=HEIGHT,
        )
        latency = round(time.time() - start, 3)

        monitor.stop()
        peak_vram_mib = monitor.peak_mib

        image = result.images[0]
        image.save(image_path)

        success = True
        print(f"Saved: {image_path}")
        print(f"Latency: {latency}s")
        print(f"Peak VRAM: {peak_vram_mib} MiB")

    except Exception as e:
        try:
            monitor.stop()
        except Exception:
            pass
        error_message = str(e)
        print("FAILED:", error_message)

    rows.append(
        {
            "prompt_id": prompt_id,
            "width": WIDTH,
            "height": HEIGHT,
            "success": success,
            "generation_time_seconds": latency,
            "peak_vram_mib": peak_vram_mib,
            "image_path": str(image_path) if success else "",
            "error": error_message,
        }
    )

with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "prompt_id",
            "width",
            "height",
            "success",
            "generation_time_seconds",
            "peak_vram_mib",
            "image_path",
            "error",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

print("\nDone.")
print("Saved CSV:", CSV_PATH)
