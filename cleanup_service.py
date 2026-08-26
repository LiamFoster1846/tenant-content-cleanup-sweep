"""HTTP entry point called by the scheduled cleanup sweep."""

from fastapi import FastAPI

from tenant_cleanup import CleanupSweepRequest, CleanupSweepResult, run_cleanup_sweep

service = FastAPI(title="Tenant content cleanup")


@service.post("/admin/cleanup-sweep", response_model=CleanupSweepResult)
def cleanup_sweep(request: CleanupSweepRequest) -> CleanupSweepResult:
    return run_cleanup_sweep(request)

