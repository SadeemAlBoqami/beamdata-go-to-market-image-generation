import json, csv, base64, time, uuid, subprocess, threading
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import Request, urlopen

API = "http://127.0.0.1:8092/v1/images/generations"
MODEL = "Tongyi-MAI/Z-Image-Turbo"

PROMPTS_FILE = Path("benchmark/prompts/benchmark_prompts.json")
OUT_DIR = Path("benchmark/results/baseline/512/images/z-image-turbo-w4")
CSV_PATH = Path("benchmark/results/baseline/512/z-image-turbo-w4_results.csv")

RUN_ID = str(uuid.uuid4())

def gpu_mem():
    try:
        return int(subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used",
             "--format=csv,noheader,nounits"],
            text=True
        ).strip().splitlines()[0])
    except:
        return 0

data = json.loads(PROMPTS_FILE.read_text())
if isinstance(data, dict):
    data = data.get("prompts", list(data.values()))

OUT_DIR.mkdir(parents=True, exist_ok=True)

with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
    fields = [
        "run_id","prompt_id","prompt","category","model",
        "width","height","generation_time_seconds",
        "peak_vram_mib","success","error","image_path","timestamp"
    ]

    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()

    for i, x in enumerate(data, 1):
        pid = x.get("prompt_id") or x.get("id")
        prompt = x.get("prompt") or x.get("text")
        category = x.get("category", "")

        print(f"\n[{i}/25] {pid}")

        peak = [gpu_mem()]
        stop = threading.Event()

        def monitor():
            while not stop.is_set():
                peak[0] = max(peak[0], gpu_mem())
                time.sleep(0.1)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

        start = time.perf_counter()
        success = False
        error = ""
        image_path = ""

        try:
            payload = json.dumps({
                "model": MODEL,
                "prompt": prompt,
                "size": "512x512",
                "seed": 42
            }).encode()

            req = Request(
                API,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urlopen(req, timeout=300) as r:
                response = json.loads(r.read())

            img = base64.b64decode(response["data"][0]["b64_json"])

            path = OUT_DIR / f"{pid}.png"
            path.write_bytes(img)

            image_path = str(path)
            success = True

        except Exception as e:
            error = str(e)

        elapsed = time.perf_counter() - start
        stop.set()
        t.join()

        writer.writerow({
            "run_id": RUN_ID,
            "prompt_id": pid,
            "prompt": prompt,
            "category": category,
            "model": MODEL,
            "width": 512,
            "height": 512,
            "generation_time_seconds": round(elapsed, 3),
            "peak_vram_mib": peak[0],
            "success": success,
            "error": error,
            "image_path": image_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        f.flush()

        print(
            f"success={success} | "
            f"time={elapsed:.3f}s | "
            f"peak_vram={peak[0]} MiB"
        )

print("\nDONE")
print("run_id:", RUN_ID)
print("csv:", CSV_PATH)
