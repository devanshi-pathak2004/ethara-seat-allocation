# Ethara Seat Allocation & Project Mapping System

A full-stack application that manages seat allocation, project mapping and
new-joiner onboarding for **~5,000 Ethara employees** across 5 floors, 20 zones
and 6,000 seats — with a natural-language **AI assistant** for seat & project
queries.

![Stack](https://img.shields.io/badge/FastAPI-Python%203.12-009688)
![Frontend](https://img.shields.io/badge/React%2018-Vite%20%2B%20Tailwind-4f46e5)
![DB](https://img.shields.io/badge/DB-SQLite%20%2F%20PostgreSQL-336791)
![Tests](https://img.shields.io/badge/tests-11%20passing-brightgreen)

---

## ✨ Features

| Area | What it does |
|------|--------------|
| **Dashboard** | Total employees, seats, occupied / available / reserved / maintenance, project-wise & floor-wise utilization, pending new joiners — with live charts. |
| **Employee management** | Full CRUD, search by name/code/email, filter by project & allocation status, soft-delete (deactivate). |
| **Project mapping** | 11 projects, each employee mapped to one active project; drill into a project's team & their seats. |
| **Seat allocation** | Create seats, browse a filterable seat grid, allocate / release, duplicate-allocation prevention. |
| **New-joiner allocation** | Add an employee, get smart seat suggestions (near their project team), auto-allocate best seat, or pick manually; alternate-zone fallback. |
| **Search & filter** | By employee name/ID/email, project, floor, zone and seat status. |
| **AI assistant** | Rule-based natural-language engine (no API key needed) answering seat, project, availability, neighbour and utilization questions. |

---

## 🏗️ Architecture

```
┌──────────────────────────┐        REST/JSON        ┌───────────────────────────┐
│  React 18 + Vite + TW     │  ───────────────────▶  │  FastAPI (Python 3.12)     │
│  Dashboard · Employees ·  │                         │  Routers · Services ·      │
│  Seats · Projects · AI    │  ◀───────────────────  │  AI intent parser          │
└──────────────────────────┘                         └────────────┬──────────────┘
                                                                   │ SQLAlchemy ORM
                                                          ┌────────▼─────────┐
                                                          │ SQLite / Postgres │
                                                          │ employees·projects│
                                                          │ seats·allocations │
                                                          └───────────────────┘
```

- **Backend** — FastAPI + SQLAlchemy 2.0. Business rules live in one place
  (`app/services.py`) so REST endpoints and the AI assistant share the exact
  same allocation logic.
- **Database** — SQLite by default (zero-config local demo); set `DATABASE_URL`
  to a Postgres URL for production. The same code runs on both.
- **Frontend** — React + Vite + Tailwind, Recharts for charts, React Router.

---

## 🚀 Quick start (local)

### 1. Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m app.seed          # generate 5k employees / 6k seats / 11 projects
uvicorn app.main:app --reload --port 8000
```

- API: <http://localhost:8000>
- Swagger docs: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

> **Note on Python version:** the project targets **Python 3.12**. Python 3.14
> is too new for some pinned wheels (pydantic-core). Use 3.12 or 3.13.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # set VITE_API_URL if your API isn't on :8000
npm run dev
```

- App: <http://localhost:5173>

### 3. Docker (one command)

```bash
docker compose up --build
# frontend → http://localhost:5173   backend → http://localhost:8000/docs
```

---

## 🌱 Seed data

`python -m app.seed` produces (all assessment targets met):

| Metric | Value |
|--------|-------|
| Employees | **5,000** |
| Projects | **11** |
| Seats total | **6,000** (5 floors × 4 zones × 12 bays × 25) |
| Occupied | 4,950 |
| Available | 800 (spread evenly across floors) |
| Reserved | 150 |
| Maintenance | 100 |
| Pending allocation (new joiners) | 50 |

A well-known demo employee is always created: **`amit@ethara.ai`** (Amit Sharma).
Sample CSV exports live in [`sample_data/`](./sample_data).

---

## 🔌 API endpoints

Full interactive docs at **`/docs`** (Swagger). Summary:

### Employees
| Method | Path | Description |
|--------|------|-------------|
| POST | `/employees` | Create employee (auto employee_code, duplicate-email guard) |
| GET | `/employees` | List / search / filter (`search`, `project_id`, `status`, `allocation_status`) |
| GET | `/employees/{id}` | Get one employee (with seat & project) |
| PUT | `/employees/{id}` | Update employee |
| DELETE | `/employees/{id}` | Deactivate (soft-delete + release seat) |

### Projects
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List projects |
| GET | `/projects/{id}` | Get project |
| GET | `/projects/{id}/employees` | List employees in a project |

### Seats
| Method | Path | Description |
|--------|------|-------------|
| POST | `/seats` | Create seat (duplicate floor/zone/number guard) |
| GET | `/seats` | List / filter (`floor`, `zone`, `status`, `search`) |
| GET | `/seats/available` | List available seats |
| POST | `/seats/allocate` | Allocate seat (explicit `seat_id` or auto-suggest near team) |
| POST | `/seats/release` | Release seat (by `seat_id` or `employee_id`) |

### Dashboard
| Method | Path | Description |
|--------|------|-------------|
| GET | `/dashboard/summary` | Totals, seat status counts, utilization %, pending |
| GET | `/dashboard/project-utilization` | Employees & allocated seats per project |
| GET | `/dashboard/floor-utilization` | Seat status per floor + occupancy % |

### AI Assistant
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/query` | Natural-language query → answer |

**Example**

```bash
curl -X POST http://localhost:8000/ai/query \
  -H 'Content-Type: application/json' \
  -d '{"query":"Where is my seat? My email is amit@ethara.ai"}'
```
```json
{
  "answer": "Amit Sharma is seated at Floor 1, Zone D, Bay 1, Seat D1-06. Assigned project: Mydreed.",
  "intent": "seat_lookup",
  "data": { "employee": "Amit Sharma", "seat": "D1-06", "floor": 1, "zone": "D", "bay": 1, "project": "Mydreed" }
}
```

The assistant also handles: *"Which project is X on?"*, *"Show available seats on
Floor 3"*, *"Who is sitting near X?"*, *"How many seats are occupied for Project
Indigo?"*.

---

## 📐 Core business rules (all enforced)

1. One employee → only one active seat.
2. One seat → only one active employee.
3. Released seats become **Available** again.
4. Reserved / Maintenance seats cannot be allocated.
5. New joiners are prioritised for seats **near their project team**; if the
   preferred zone is full, an alternate zone is suggested.
6. Duplicate employee email is rejected (409).
7. Duplicate seat number on the same floor/zone is rejected (409).
8. Dashboard reflects every allocation / release immediately.

These rules are covered by the automated test suite (`backend/tests/`).

---

## 🧪 Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q          # 11 tests, isolated temp DB
```

Tests cover CRUD, duplicate guards, allocation, double-allocation prevention,
one-seat-one-employee, reserved-seat rejection, release→available, auto-suggest,
dashboard counts and the AI assistant.

---

## 🗂️ Project structure

```
assessment/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app + CORS + routers
│   │   ├── database.py       # engine/session (SQLite or Postgres)
│   │   ├── models.py         # SQLAlchemy models (4 tables)
│   │   ├── schemas.py        # Pydantic request/response models
│   │   ├── services.py       # allocation engine + serializers (shared)
│   │   ├── ai.py             # natural-language intent parser
│   │   ├── seed.py           # 5k/6k/11 demo data generator
│   │   ├── seed_if_empty.py  # deploy-safe conditional seeding
│   │   └── routers/          # employees, projects, seats, dashboard, ai
│   ├── tests/                # pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/            # Dashboard, Employees, Seats, Projects, Assistant
│   │   ├── components/ui.jsx # StatCard, Modal, Badge, Toast…
│   │   ├── lib/api.js        # API client
│   │   └── App.jsx           # layout + routing
│   ├── package.json
│   └── Dockerfile
├── sample_data/              # CSV exports of seed data
├── schema.sql                # generated DDL
├── docker-compose.yml
├── render.yaml               # Render blueprint (backend)
├── README.md
├── AI_PROMPTS.md             # required AI-usage documentation
├── DEPLOYMENT.md             # deployment notes
└── DEBUGGING.md              # debugging notes
```

---

## ☁️ Deployment

See **[DEPLOYMENT.md](./DEPLOYMENT.md)** for step-by-step Render (backend) +
Vercel/Netlify (frontend) instructions. TL;DR:

- **Backend → Render**: repo includes `render.yaml`; it builds, seeds and serves.
- **Frontend → Vercel/Netlify**: set `VITE_API_URL` to the live backend URL; build
  command `npm run build`, output `dist`.

---

## 🔐 Authentication

This demo does not gate the UI behind login (the brief lists auth as optional).
A well-known demo identity is seeded for the AI assistant and screenshots:

```
Demo employee email: amit@ethara.ai
```

If auth were added, credentials would be documented here.
