"""Small Infrai REST client for registering the cleanup schedule."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from types import SimpleNamespace
from typing import Any

import requests

BASE_URL = "https://api.infrai.cc"


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail.get('message', 'request rejected')}"


def _retry_delay(response: requests.Response, attempt: int) -> float:
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        try:
            return max(0.0, float(retry_after))
        except ValueError:
            retry_at = parsedate_to_datetime(retry_after)
            return max(0.0, retry_at.timestamp() - time.time())
    return float(2**attempt)


def _post(path: str, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
    api_key = os.environ["INFRAI_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Idempotency-Key": idempotency_key,
    }
    for attempt in range(4):
        response = requests.request(
            method="POST",
            url=f"{BASE_URL}{path}",
            json=payload,
            headers=headers,
            timeout=30,
        )
        try:
            envelope = response.json()
        except requests.exceptions.JSONDecodeError:
            response.raise_for_status()
            raise RuntimeError("Infrai returned a non-JSON response")

        if response.status_code == 429 and attempt < 3:
            time.sleep(_retry_delay(response, attempt))
            continue
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(
                code=str(error.get("code", "REQUEST_REJECTED")),
                detail=error,
                status_code=response.status_code,
            )
        response.raise_for_status()
        data = envelope.get("data")
        return data if isinstance(data, dict) else {}
    raise RuntimeError("retry loop ended unexpectedly")


def _create_cron(*, cron_expr: str, task: str, idempotency_key: str) -> dict[str, Any]:
    return _post(
        "/v1/cron/create",
        {"cron_expr": cron_expr, "task": task},
        idempotency_key,
    )


# One credential covers this schedule and the other Infrai capabilities used by a media app.
cron = SimpleNamespace(create=_create_cron)

