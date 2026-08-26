"""Business rules for archiving stale tenant content records."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, Field


class AccountLifecycle(str, Enum):
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    CANCELED = "canceled"
    ARCHIVED = "archived"


class TenantRecord(BaseModel):
    tenant_id: str = Field(min_length=1)
    workspace_name: str = Field(min_length=1)
    lifecycle: AccountLifecycle
    last_content_activity_at: datetime


class CleanupSweepRequest(BaseModel):
    records: list[TenantRecord]
    inactive_days: int = Field(default=90, ge=1, le=3650)
    sweep_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CleanupSweepResult(BaseModel):
    archived_tenant_ids: list[str]
    retained_tenant_ids: list[str]
    cutoff: datetime


def run_cleanup_sweep(request: CleanupSweepRequest) -> CleanupSweepResult:
    cutoff = request.sweep_at - timedelta(days=request.inactive_days)
    archived: list[str] = []
    retained: list[str] = []

    for record in request.records:
        should_archive = (
            record.lifecycle is AccountLifecycle.CANCELED
            and record.last_content_activity_at <= cutoff
        )
        (archived if should_archive else retained).append(record.tenant_id)

    return CleanupSweepResult(
        archived_tenant_ids=archived,
        retained_tenant_ids=retained,
        cutoff=cutoff,
    )

