# Deployment Validation

Date: 2026-09-22

## FLUX.2 Klein 4B Q4_K_M

- Runtime: vLLM-Omni
- Quantization: GGUF Q4_K_M
- Containerized: Yes
- API authentication: Bearer token
- Request without token: 401 Unauthorized
- Request with valid token: 200 OK
- Authenticated 512x512 image generation: Successful

Smoke test:
`benchmark/results/open_source/flux2-klein/q4_k_m/512/smoke-test/`

## Z-Image-Turbo W4

- Runtime: vLLM-Omni
- Quantization: BitsAndBytes W4
- Containerized: Yes
- API authentication: Bearer token
- Request without token: 401 Unauthorized
- Request with valid token: 200 OK
- Authenticated 512x512 image generation: Successful

Smoke test:
`benchmark/results/open_source/z-image-turbo/w4/512/smoke-test/`

## Authentication

Both selected inference services require:

`Authorization: Bearer <API_TOKEN>`

The API token is supplied through the `API_TOKEN` environment variable and is not stored in the repository or container image.
