FROM vllm/vllm-omni:v0.28.0

EXPOSE 8000

CMD ["vllm", "serve", "black-forest-labs/FLUX.2-klein-4B", "--omni", "--host", "0.0.0.0", "--port", "8000"]
