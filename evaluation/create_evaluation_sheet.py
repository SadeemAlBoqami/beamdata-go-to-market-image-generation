import pandas as pd

INPUT = "../benchmark/results/benchmark_results.csv"

df = pd.read_csv(INPUT)

# only tue images
df = df[df["success"] == True].copy()

# re-arrange
df = df.sort_values(["prompt_id", "provider"]).reset_index(drop=True)

# IDs without model name
df["image_id"] = [
    f"IMG{i:03d}" for i in range(1, len(df) + 1)
]

# mapping file
mapping = df[
    ["image_id", "prompt_id", "provider", "model", "image_url"]
].copy()

mapping.to_csv("image_mapping.csv", index=False)

# evaluation file
evaluation = df[
    ["image_id", "prompt_id", "prompt", "image_url"]
].copy()

evaluation["quality"] = ""
evaluation["prompt_adherence"] = ""
evaluation["composition"] = ""
evaluation["marketing_usefulness"] = ""
evaluation["visual_appeal"] = ""
evaluation["text_accuracy"] = ""
evaluation["people_anatomy"] = ""
evaluation["object_accuracy"] = ""
evaluation["notes"] = ""

evaluation.to_csv("evaluation_input.csv", index=False)

print(f"Created evaluation sheet for {len(evaluation)} images.")
