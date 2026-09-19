FROM vllm/vllm-omni:v0.28.0

EXPOSE 8000

CMD ["vllm", "serve", "stabilityai/stable-diffusion-3.5-medium", "--omni", "--host", "0.0.0.0", "--port", "8000"]
