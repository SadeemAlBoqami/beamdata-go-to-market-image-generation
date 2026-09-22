FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:/root/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && uv python install 3.12.14 \
    && uv venv /opt/venv --python 3.12.14

RUN uv pip install \
    "https://github.com/vllm-project/vllm/releases/download/v0.29.0/vllm-0.29.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl"

RUN git clone https://github.com/vllm-project/vllm-omni.git /opt/vllm-omni \
    && cd /opt/vllm-omni \
    && git fetch origin pull/7759/head:validated-runtime \
    && git checkout 3d6a1c4d9a0a09d8392bda3a54f8dfb890d5fb05 \
    && uv pip install -e .

RUN uv pip install "bitsandbytes==0.50.2"

WORKDIR /app
COPY serve.sh /app/serve.sh

RUN chmod +x /app/serve.sh

EXPOSE 8000

ENTRYPOINT ["/app/serve.sh"]
