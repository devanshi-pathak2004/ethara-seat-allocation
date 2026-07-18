"""End-to-end API tests covering the core business rules.

Run from the backend/ directory:
    pytest -q
Uses an isolated temporary SQLite database so it never touches demo data.
"""
import os
import tempfile

import pytest

# Point the app at a throwaway DB *before* importing it.
_TMP = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP.name}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _make_project():
    return client.post("/projects", json={"name": "Talos"}).json()


def _make_employee(email="amit@ethara.ai", project_id=None):
    return client.post(
        "/employees",
        json={"name": "Amit Sharma", "email": email, "project_id": project_id},
    )


def _make_seat(floor=2, zone="B", bay=4, seat_number="B4-23"):
    return client.post(
        "/seats",
        json={"floor": floor, "zone": zone, "bay": bay, "seat_number": seat_number},
    )


def test_create_and_list_employee():
    _make_project()
    r = _make_employee()
    assert r.status_code == 201
    body = r.json()
    assert body["employee_code"].startswith("ETH")
    assert body["allocation_status"] == "Pending"

    lst = client.get("/employees").json()
    assert lst["total"] == 1


def test_duplicate_email_rejected():
    _make_employee()
    dup = _make_employee()  # same email
    assert dup.status_code == 409


def test_duplicate_seat_rejected():
    _make_seat()
    dup = _make_seat()  # same floor/zone/number
    assert dup.status_code == 409


def test_allocate_and_prevent_double_allocation():
    proj = _make_project()
    emp = _make_employee(project_id=proj["id"]).json()
    seat = _make_seat().json()

    ok = client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": seat["id"]})
    assert ok.status_code == 200
    assert ok.json()["seat"]["status"] == "Occupied"

    # Same employee cannot hold two seats.
    seat2 = _make_seat(seat_number="B4-24").json()
    again = client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": seat2["id"]})
    assert again.status_code == 400


def test_one_seat_one_employee():
    e1 = _make_employee(email="a@ethara.ai").json()
    e2 = _make_employee(email="b@ethara.ai").json()
    seat = _make_seat().json()

    client.post("/seats/allocate", json={"employee_id": e1["id"], "seat_id": seat["id"]})
    clash = client.post("/seats/allocate", json={"employee_id": e2["id"], "seat_id": seat["id"]})
    assert clash.status_code == 400  # seat already occupied


def test_reserved_seat_not_allocatable():
    emp = _make_employee().json()
    seat = _make_seat().json()
    client.post(f"/seats", json={})  # noop guard
    # Force the seat to Reserved via a fresh reserved seat.
    reserved = client.post(
        "/seats",
        json={"floor": 3, "zone": "A", "bay": 1, "seat_number": "A1-01", "status": "Reserved"},
    ).json()
    res = client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": reserved["id"]})
    assert res.status_code == 400


def test_release_makes_seat_available_again():
    emp = _make_employee().json()
    seat = _make_seat().json()
    client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": seat["id"]})

    rel = client.post("/seats/release", json={"employee_id": emp["id"]})
    assert rel.status_code == 200
    assert rel.json()["seat"]["status"] == "Available"

    # Now re-allocatable.
    again = client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": seat["id"]})
    assert again.status_code == 200


def test_auto_suggest_allocation():
    emp = _make_employee().json()
    _make_seat()
    res = client.post("/seats/allocate", json={"employee_id": emp["id"]})  # no seat_id
    assert res.status_code == 200
    assert res.json()["seat"]["seat_number"] == "B4-23"


def test_dashboard_summary_updates():
    _make_employee()
    _make_seat()
    before = client.get("/dashboard/summary").json()
    assert before["total_employees"] == 1
    assert before["available_seats"] == 1
    assert before["pending_allocation"] == 1


def test_ai_seat_lookup():
    proj = _make_project()
    emp = _make_employee(project_id=proj["id"]).json()
    seat = _make_seat().json()
    client.post("/seats/allocate", json={"employee_id": emp["id"], "seat_id": seat["id"]})

    r = client.post("/ai/query", json={"query": "Where is my seat? My email is amit@ethara.ai"})
    assert r.status_code == 200
    ans = r.json()["answer"]
    assert "B4-23" in ans and "Talos" in ans


def test_ai_available_seats():
    _make_seat()
    r = client.post("/ai/query", json={"query": "Show all available seats on Floor 2"})
    assert "available seats" in r.json()["answer"].lower()
