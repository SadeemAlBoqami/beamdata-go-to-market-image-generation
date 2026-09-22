FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:/root/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv + exact Python version
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv python install 3.12.14 \
    && /root/.local/bin/uv venv /opt/venv --python 3.12.14

# Exact vLLM wheel that succeeded on the server
RUN /root/.local/bin/uv pip install \
    --python /opt/venv/bin/python \
    "https://github.com/vllm-project/vllm/releases/download/v0.29.0/vllm-0.29.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl"

# Exact vLLM-Omni commit that succeeded
RUN git clone https://github.com/vllm-project/vllm-omni.git /opt/vllm-omni \
    && cd /opt/vllm-omni \
    && git fetch origin pull/7759/head:validated-runtime \
    && git checkout 3d6a1c4d9a0a09d8392bda3a54f8dfb890d5fb05 \
    && /root/.local/bin/uv pip install \
       --python /opt/venv/bin/python \
       -e .

# Exact quantization dependency used in successful run
RUN /root/.local/bin/uv pip install \
    --python /opt/venv/bin/python \
    "bitsandbytes==0.50.2"

# Fail the Docker build immediately if versions drift
RUN /opt/venv/bin/python - <<'PY'
import torch
import vllm
import bitsandbytes

print("torch:", torch.__version__)
print("vllm:", vllm.__version__)
print("bitsandbytes:", bitsandbytes.__version__)

assert vllm.__version__ == "0.29.0+cu129"
assert bitsandbytes.__version__ == "0.50.2"
PY

WORKDIR /app

COPY serve.sh /app/serve.sh
RUN chmod +x /app/serve.sh

EXPOSE 8000

ENTRYPOINT ["/app/serve.sh"]
