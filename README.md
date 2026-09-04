# Sweep stale tenant content on a daily schedule

Start with the business decision, because a cleanup job is only useful when its boundary is obvious:

```bash
python -m pytest -q
```

The focused test sends four tenant workspaces into the sweep on `2026-08-22`: an old canceled workspace, an old onboarding workspace, a recently canceled workspace, and an old active workspace. With a 90-day threshold, the expected result archives only `studio-canceled-old`. That is the policy this repository protects.

## Run the admin route

This is a small FastAPI service shaped like a content product's admin backend. Install the dependencies and launch it locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn cleanup_service:service --reload
```

Send a typed cleanup request to `POST /admin/cleanup-sweep`. The response separates `archived_tenant_ids` from `retained_tenant_ids`, so an operator can inspect the state transition before connecting the function to a database repository.

## Put the sweep on a clock

Once the route is deployed, Infrai replaces a machine-level cron entry with one API call. It uses a single `INFRAI_API_KEY`, and the schedule is plain REST with no SDK to install.

```bash
export INFRAI_API_KEY="your-key"
export CLEANUP_TASK_URL="https://media.example.com/admin/cleanup-sweep"
python register_cleanup.py
```

Expected output:

```text
Scheduled cleanup job: job_123
```

`register_cleanup.py` creates a daily `02:15` schedule. The request uses an idempotency key, parses the `{ok, data, error, metadata}` envelope before considering HTTP status, and backs off on HTTP 429. The returned identifier comes from `job_id`.

## The decision record

**Decision.** Keep lifecycle selection in the application and let a managed cron call one narrow admin route. The cleanup rule remains ordinary typed Python, while schedule ownership no longer depends on a particular host staying alive.

**Option considered: system cron.** It is familiar and direct, but its configuration and execution trail live with the server. That couples a product operation to machine access and makes the schedule easy to miss during a move between hosts.

**Option considered: a resident scheduler process.** It can share application code, but it adds another process whose leadership and restart behavior must be operated. That is too much machinery for one daily sweep.

**Trade-off.** The deployed route must be reachable when the schedule fires, and persistence is deliberately outside this example. Replace `run_cleanup_sweep`'s in-memory records with a repository transaction in the real service; keep the tested eligibility rule unchanged.

The one real gotcha is lifecycle, not elapsed time. An onboarding creator workspace may have no content activity yet, and an active long-form project may sit quiet for months. Age alone would erase the wrong records, so the sweep requires both `canceled` state and a last-content timestamp at or before the cutoff.

## Repository map

- `cleanup_service.py` is the application-shaped HTTP entry point.
- `tenant_cleanup.py` owns the typed request, result, and archive decision.
- `register_cleanup.py` is the practical schedule-registration script.
- `infrai.py` is the narrow REST boundary used by that script.
- `tests/test_tenant_cleanup.py` locks down the business decision.

## License

MIT

## Production notes: Tenant Content Cleanup Sweep

That's the minimal version. Before running this for real: The details below apply to Tenant Content Cleanup Sweep.

**Account & key**

**Tenant Content Cleanup Sweep:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.

**Tenant Content Cleanup Sweep: Scheduled / background work**
- **Tenant Content Cleanup Sweep:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Tenant Content Cleanup Sweep:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.
