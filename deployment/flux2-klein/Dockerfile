FROM nvidia/cuda:12.9.1-runtime-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/root/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv python install 3.12.14 \
    && /root/.local/bin/uv venv /opt/venv --python 3.12.14

RUN /root/.local/bin/uv pip install \
    --python /opt/venv/bin/python \
    "https://github.com/vllm-project/vllm/releases/download/v0.29.0/vllm-0.29.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl"

RUN git clone https://github.com/vllm-project/vllm-omni.git /opt/vllm-omni \
    && cd /opt/vllm-omni \
    && git fetch origin pull/7759/head:validated-runtime \
    && git checkout 3d6a1c4d9a0a09d8392bda3a54f8dfb890d5fb05 \
    && /root/.local/bin/uv pip install \
       --python /opt/venv/bin/python \
       -e .

RUN /root/.local/bin/uv pip install \
    --python /opt/venv/bin/python \
    "vllm-gguf-plugin==0.0.5"

# Re-pin exact CUDA 12.9 PyTorch stack
RUN /root/.local/bin/uv pip install \
    --python /opt/venv/bin/python \
    --index-url https://download.pytorch.org/whl/cu129 \
    "torch==2.13.0+cu129" \
    "torchvision==0.28.0+cu129" \
    "torchaudio==2.11.0+cu129"

# Verify reproducible runtime versions
RUN /opt/venv/bin/python - <<'PYVERIFY'
from importlib.metadata import version

packages = {
    "torch": "2.13.0+cu129",
    "torchvision": "0.28.0+cu129",
    "torchaudio": "2.11.0+cu129",
    "vllm": "0.29.0+cu129",
    "vllm-gguf-plugin": "0.0.5",
}

for package, expected in packages.items():
    actual = version(package)
    print(f"{package}: {actual}")
    assert actual == expected, f"{package}: expected {expected}, got {actual}"

print("Package version verification passed.")
PYVERIFY

WORKDIR /app
COPY serve.sh /app/serve.sh
RUN chmod +x /app/serve.sh

EXPOSE 8000

ENTRYPOINT ["/app/serve.sh"]
