# AI_PROMPTS.md

Documentation of AI tool usage for the **Ethara Seat Allocation & Project
Mapping System**, as required by the assessment.

- **AI tool used:** Claude (Anthropic) via an agentic coding assistant.
- **How it was used:** to scaffold the FastAPI backend, SQLAlchemy models, the
  seed generator, the rule-based AI assistant, and the React + Tailwind frontend;
  then to debug, test and document.
- **Validation approach:** every AI-generated piece was run locally — the seed
  script, the full pytest suite (11 tests), and live `curl` calls against the
  API — before being accepted. Details per section below.

---

## Prompt flow (the 10 prompts actually used)

### Prompt 1 — Architecture / Planning
> "I'm building a seat-allocation system for ~5,000 employees at Ethara. It needs
> employee management, project mapping, seat allocation, a new-joiner flow,
> search/filter, a dashboard, and a natural-language AI assistant. Recommend a
> clean full-stack architecture using FastAPI + SQLAlchemy + SQLite (Postgres-
> ready) and React + Vite + Tailwind. Keep all allocation business rules in one
> shared module so the REST API and the AI assistant reuse the same logic."

### Prompt 2 — Database design
> "Design the SQLAlchemy models for four tables: projects, employees, seats,
> seat_allocations. Employees map to one project; a seat has floor/zone/bay/
> seat_number/status; allocations track active vs released with dates. Add the
> right unique constraints: employee email unique, and no duplicate seat number
> on the same floor+zone. Add indexes for the columns we'll search/filter on."

### Prompt 3 — Backend APIs
> "Implement FastAPI routers for all required endpoints: employees CRUD + search/
> filter, projects (+ list employees in project), seats (create/list/available/
> allocate/release), dashboard (summary / project-utilization / floor-utilization),
> and POST /ai/query. Use Pydantic v2 schemas and return derived fields like
> allocation_status and the employee's current seat."

### Prompt 4 — Seat allocation logic
> "Write a seat allocation engine enforcing: one active seat per employee, one
> active employee per seat, reserved/maintenance seats not allocatable, released
> seats become available. For new joiners, auto-suggest the best available seat
> prioritising the employee's project cluster (team proximity), then preferred
> floor, then any available seat as an alternate-zone fallback."

### Prompt 5 — AI assistant
> "Build a natural-language assistant that works WITHOUT any external API key
> (rule-based intent parser as the reliable fallback the brief allows). It must
> answer: where is employee X seated, which project is X on, available seats on a
> floor, who is sitting near X, and how many seats are occupied for project Y.
> Parse the employee by email first, then by name. Return {answer, intent, data}."

### Prompt 6 — Frontend
> "Create an attractive React + Vite + Tailwind UI with a sidebar layout and five
> pages: Dashboard (stat cards + Recharts donut/bar + floor occupancy bars),
> Employees (search/filter table, add-employee modal, allocate/release modal with
> seat suggestions), Seats (filterable seat-card grid with release), Projects
> (cards + team drill-down modal), and an AI Assistant chat page with suggested
> prompts. Use a polished indigo brand palette, rounded cards, soft shadows."

### Prompt 7 — Testing
> "Write a pytest suite using FastAPI TestClient against an isolated temp SQLite
> DB that verifies each core business rule: create/list employee, duplicate email
> rejected, duplicate seat rejected, allocate + prevent double allocation, one
> seat one employee, reserved seat not allocatable, release makes seat available,
> auto-suggest allocation, dashboard summary counts, and the AI seat lookup."

### Prompt 8 — Debugging
> "Two bugs: (1) filtering employees by allocation_status=Pending returns nothing
> when combined with pagination; (2) 'available seats on Floor 3' returns 0
> because all leftover seats bunch on the top floor. Fix both. Also remove
> datetime.utcnow() deprecation warnings and the SQLAlchemy subquery-coercion
> warning."

### Prompt 9 — Deployment
> "Make this deployable: a backend Dockerfile and a render.yaml that installs,
> seeds only if the DB is empty, and serves with uvicorn; a frontend Dockerfile
> (nginx) plus vercel.json and netlify.toml with SPA fallback; and a docker-
> compose for the whole stack. Make DATABASE_URL and CORS_ORIGINS configurable."

### Prompt 10 — Refactoring
> "Extract a shared utils.utcnow() helper, move all serialization + allocation
> into services.py so routers stay thin, and switch raw subqueries to select()
> to silence coercion warnings. Keep functions small and commented."

---

## What the AI generated **correctly**

- Clean SQLAlchemy models with the correct unique constraints and relationships.
- The full set of required REST endpoints with sensible Pydantic schemas.
- A shared allocation engine reused by both the API and the AI assistant.
- A rule-based AI intent parser that answers every question in the brief and
  needs **no API key** — including email- and name-based employee lookup.
- A polished, responsive React/Tailwind UI with working charts, modals and
  toasts; the production build compiled with all 2,206 modules resolving.
- The seed generator hitting **every** required data target on the first run.
- A pytest suite that passed after the fixes below.

## What the AI generated **incorrectly** (and how it was caught)

1. **Pagination vs. derived filter bug.** The first version of
   `GET /employees` applied the `allocation_status` (Allocated/Pending) filter
   *in Python after* the SQL `LIMIT`, so `?allocation_status=Pending&limit=1`
   returned an empty list even though 50 pending employees existed.
   **Caught by:** a live `curl` that raised `IndexError: list index out of range`
   while testing the allocation flow.

2. **Available seats bunched on the top floor.** The initial allocation filled
   seats contiguously from Floor 1 upward, so all 800 leftover Available seats
   ended up on Floor 5 and *"available seats on Floor 3"* returned **0**.
   **Caught by:** querying `/seats/available?floor=N` for each floor and seeing
   0/0/0/0/800.

3. **Environment mismatch (not a code bug, but real).** The machine's default
   Python was **3.14**, for which the pinned `pydantic-core` had no wheel and
   failed to compile (PyO3 max 3.13).
   **Caught by:** the `pip install` build error.

4. **Deprecation / warning noise.** `datetime.utcnow()` (deprecated in 3.12) and
   a SQLAlchemy "Coercing Subquery into a select()" warning.
   **Caught by:** running `pytest -W error::DeprecationWarning`.

## What was **manually fixed**

1. Rewrote the `allocation_status` filter to run **at the DB level** using a
   `select()` subquery *before* pagination — so counts and pages are correct.
2. Reworked the seed allocation to **leave ~800 Available seats spread evenly**
   across all floors/zones (a computed gap-step), while still clustering each
   project's team into contiguous seat blocks.
3. Recreated the virtualenv with **Python 3.12** (Homebrew), which has prebuilt
   wheels; documented the version requirement in the README.
4. Added a `utils.utcnow()` timezone-aware helper and replaced every
   `datetime.utcnow()`; converted raw `.subquery()` calls to `select(...)`.

## How correctness was **verified**

- **Seed:** ran `python -m app.seed` and confirmed the printed summary matched
  every target (5,000 / 6,000 / 11 / 800 available / 150 reserved / 100
  maintenance / 50 pending).
- **APIs:** live `curl` against a running server for dashboard summary, employee
  search, allocate → double-allocate (expected 400) → release, duplicate-email
  (expected 409), and all five AI query types.
- **Business rules:** `pytest -q` → **11 passed**, and re-run with
  `-W error::DeprecationWarning` → still 11 passed, zero warnings.
- **Frontend:** `npm run build` succeeded (all modules transformed) and the Vite
  dev server served the app while pointed at the live backend.
- **Per-floor availability:** re-queried `/seats/available?floor=1..5` and
  confirmed ~160 available on each floor after the fix.
