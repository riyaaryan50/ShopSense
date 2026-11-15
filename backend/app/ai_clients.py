"""HTTP clients for the AI microservices.

    NLP service (Member 4)      NLP_SERVICE_URL  default http://127.0.0.1:5002
    Content-based + SVD (M1/M2) CB_SERVICE_URL   default http://127.0.0.1:5001
    Hybrid NCF service (M3)     ML_SERVICE_URL   optional, e.g. http://127.0.0.1:8000

Every call has a short timeout and raises ``ServiceUnavailable`` on failure so
routes can fall back gracefully instead of hanging the request.
"""

import logging
import os

import requests

log = logging.getLogger(__name__)

TIMEOUT = float(os.getenv("AI_SERVICE_TIMEOUT", "8"))
_http = requests.Session()


class ServiceUnavailable(Exception):
    pass


def _url(env_name, default):
    return (os.getenv(env_name) or default or "").rstrip("/")


def nlp_url():
    return _url("NLP_SERVICE_URL", "http://127.0.0.1:5002")


def cb_url():
    return _url("CB_SERVICE_URL", "http://127.0.0.1:5001")


def ml_url():
    return _url("ML_SERVICE_URL", "")


def call(method, base, path, timeout=TIMEOUT, **kwargs):
    if not base:
        raise ServiceUnavailable("service URL not configured")
    try:
        response = _http.request(method, f"{base}{path}", timeout=timeout, **kwargs)
    except requests.RequestException as error:
        log.warning("%s%s unreachable: %s", base, path, error)
        raise ServiceUnavailable(str(error)) from error
    if response.status_code >= 500:
        raise ServiceUnavailable(f"{base}{path} returned {response.status_code}")
    try:
        data = response.json()
    except ValueError as error:
        raise ServiceUnavailable("invalid JSON from service") from error
    return response.status_code, data


def notify_review_changed(product_id):
    """Fire-and-forget: tell the NLP service to drop its cached summary."""
    try:
        call("POST", nlp_url(), f"/api/nlp/reviews/{product_id}/invalidate", timeout=1)
    except ServiceUnavailable:
        pass
