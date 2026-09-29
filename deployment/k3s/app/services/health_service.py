"""Small readiness probe for deployed image APIs."""

import os

import requests

from .flux_service import FLUX_ENDPOINT, FLUX_TOKEN


def check_backend_ready(model_name: str) -> str | None:
    """Return a safe error for an unavailable backend, or None if it can be tried."""
    if model_name == "FLUX":
        endpoint, token = FLUX_ENDPOINT, FLUX_TOKEN
    else:
        endpoint = os.environ.get("ZIMAGE_ENDPOINT")
        token = os.environ.get("ZIMAGE_TOKEN")

    if not endpoint:
        return "Backend unavailable"

    health_url = endpoint.rstrip("/").removesuffix("/v1/images/generations") + "/health"
    headers = {"Authorization": f"Bearer {token}"} if token else None
    try:
        response = requests.get(health_url, headers=headers, timeout=2)
    except requests.RequestException:
        return "Backend unavailable"

    if response.status_code in (401, 403):
        return "Authentication failed"
    if response.status_code in (404, 405):
        # Some deployments serve images without exposing a health route.
        return None
    if response.status_code >= 400:
        return "Backend unavailable"
    return None
