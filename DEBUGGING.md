# Debugging Notes

Real issues encountered while building the system, how they were diagnosed, and
how they were resolved. (Mirrors the "debugging" section of `AI_PROMPTS.md`.)

---

### 1. `pydantic-core` failed to build on Python 3.14

**Symptom**
```
error: the configured Python interpreter version (3.14) is newer than
PyO3's maximum supported version (3.13) ... Failed building wheel for pydantic-core
```

**Diagnosis** — The machine's default `python3` was 3.14, which has no prebuilt
`pydantic-core` wheel; pip tried to compile from source with a Rust/PyO3 toolchain
that caps at 3.13.

**Fix** — Recreated the virtualenv with Homebrew **Python 3.12**
(`/opt/homebrew/bin/python3.12 -m venv .venv`), which installs prebuilt wheels
instantly. Documented the 3.12/3.13 requirement in the README.

---

### 2. `allocation_status=Pending` filter returned nothing with pagination

**Symptom** — Fetching a pending employee for the allocation test crashed:
```
IndexError: list index out of range
```
`GET /employees?allocation_status=Pending&limit=1` returned `items: []` although
50 pending employees existed.

**Diagnosis** — `allocation_status` is a **derived** field (an employee is
"Pending" iff they have no active allocation). The first implementation fetched a
page with SQL `LIMIT` first and *then* filtered in Python, so a page full of
"Allocated" rows was filtered down to empty.

**Fix** — Moved the filter into SQL, before pagination:
```python
allocated_ids = select(models.SeatAllocation.employee_id).where(
    models.SeatAllocation.allocation_status == "Active"
)
if allocation_status.lower() == "pending":
    q = q.filter(~models.Employee.id.in_(allocated_ids))
```
**Verified** — `?allocation_status=Pending` now reports `total: 50` and returns
real pending employees; the allocation flow test passes.

---

### 3. "Available seats on Floor 3" returned 0

**Symptom** — The AI query and `/seats/available?floor=3` both returned 0.

**Diagnosis** — The seed allocated seats contiguously from Floor 1 upward, so all
800 leftover Available seats landed on Floor 5. Availability per floor was
`0 / 0 / 0 / 0 / 800`.

**Fix** — Reworked the seed to leave Available seats **spread evenly** using a
computed gap-step across the floor/zone-sorted seat list, while still assigning
each project's employees to contiguous blocks (so team-proximity queries stay
realistic).
**Verified** — per-floor availability is now ~160 each:
```
Floor 1: 160  Floor 2: 159  Floor 3: 161  Floor 4: 160  Floor 5: 160
```

---

### 4. Port 8010 already in use during local testing

**Symptom** — `uvicorn ... --port 8010` exited with
`[Errno 48] address already in use`, and curls hit a *different* app's responses.

**Diagnosis** — An unrelated pre-existing Python process was bound to 8010.

**Fix** — Ran the dev server on **port 8020** instead (left the other process
untouched). For submission the backend uses the standard port 8000.

---

### 5. Deprecation & ORM warnings

**Symptom** — Test output carried `DeprecationWarning: datetime.utcnow()` and
`SAWarning: Coercing Subquery object into a select() for use in IN()`.

**Fix** —
- Added `app/utils.py::utcnow()` (timezone-aware) and replaced every
  `datetime.utcnow()` in models, services and seed.
- Replaced raw `.subquery()` used inside `.in_()` with explicit `select(...)`
  constructs in the dashboard and employees routers.

**Verified** — `pytest -q -W error::DeprecationWarning` → **11 passed, 0 warnings**.

---

## How to reproduce the verification

```bash
cd backend
source .venv/bin/activate
python -m app.seed                       # prints target summary
pytest -q -W error::DeprecationWarning   # 11 passed, no warnings
uvicorn app.main:app --reload --port 8000
# then, in another shell:
curl -s localhost:8000/dashboard/summary
curl -s -X POST localhost:8000/ai/query -H 'Content-Type: application/json' \
  -d '{"query":"Where is my seat? My email is amit@ethara.ai"}'
```
