"""Register the daily call to the tenant cleanup route."""

import os
from urllib.parse import urlparse

import infrai


def register_cleanup() -> str:
    task_url = os.environ["CLEANUP_TASK_URL"]
    parsed = urlparse(task_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("CLEANUP_TASK_URL must be an absolute HTTP URL")

    result = infrai.cron.create(
        cron_expr="15 2 * * *",
        task=task_url,
        idempotency_key="tenant-content-cleanup-daily-v1",
    )
    job_id = result.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        raise RuntimeError("create response did not contain job_id")
    return job_id


if __name__ == "__main__":
    print(f"Scheduled cleanup job: {register_cleanup()}")

