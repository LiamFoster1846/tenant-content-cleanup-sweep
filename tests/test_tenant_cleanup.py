from datetime import datetime, timezone

from tenant_cleanup import CleanupSweepRequest, run_cleanup_sweep


def test_sweep_archives_only_stale_canceled_tenants() -> None:
    request = CleanupSweepRequest.model_validate(
        {
            "inactive_days": 90,
            "sweep_at": "2026-08-22T12:00:00Z",
            "records": [
                {
                    "tenant_id": "studio-canceled-old",
                    "workspace_name": "Archive Studio",
                    "lifecycle": "canceled",
                    "last_content_activity_at": "2026-04-01T09:00:00Z",
                },
                {
                    "tenant_id": "studio-onboarding-old",
                    "workspace_name": "New Creator Room",
                    "lifecycle": "onboarding",
                    "last_content_activity_at": "2026-03-01T09:00:00Z",
                },
                {
                    "tenant_id": "studio-canceled-recent",
                    "workspace_name": "Recent Edit Room",
                    "lifecycle": "canceled",
                    "last_content_activity_at": "2026-08-01T09:00:00Z",
                },
                {
                    "tenant_id": "studio-active-old",
                    "workspace_name": "Documentary Desk",
                    "lifecycle": "active",
                    "last_content_activity_at": "2026-01-01T09:00:00Z",
                },
            ],
        }
    )

    result = run_cleanup_sweep(request)

    assert result.archived_tenant_ids == ["studio-canceled-old"]
    assert result.retained_tenant_ids == [
        "studio-onboarding-old",
        "studio-canceled-recent",
        "studio-active-old",
    ]
    assert result.cutoff == datetime(2026, 5, 24, 12, 0, tzinfo=timezone.utc)

