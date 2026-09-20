FROM vllm/vllm-omni:v0.28.0

EXPOSE 8000

CMD ["vllm", "serve", "stabilityai/stable-diffusion-xl-base-1.0", "--omni", "--host", "0.0.0.0", "--port", "8000"]
