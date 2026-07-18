"""Natural-language assistant for seat / project queries.

Design: a deterministic **intent parser** handles every question the brief
asks for and works with ZERO external dependencies or API keys. If an
``OPENAI_API_KEY`` is present we additionally expose an LLM-backed path, but
the rule-based engine is always the reliable fallback (as the brief allows).
"""
import re
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from . import models, services

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
FLOOR_RE = re.compile(r"floor\s*(\d+)", re.I)


def _seat_phrase(seat: models.Seat) -> str:
    return f"Floor {seat.floor}, Zone {seat.zone}, Bay {seat.bay}, Seat {seat.seat_number}"


def _find_employee(db: Session, text: str) -> Optional[models.Employee]:
    """Locate an employee by email first, then by a name mentioned in the text."""
    email_match = EMAIL_RE.search(text)
    if email_match:
        emp = (
            db.query(models.Employee)
            .filter(func.lower(models.Employee.email) == email_match.group(0).lower())
            .first()
        )
        if emp:
            return emp

    # Try matching against known employee names (longest names first).
    lowered = text.lower()
    names = db.query(models.Employee.id, models.Employee.name).all()
    best = None
    for emp_id, name in names:
        first = name.split()[0].lower()
        if re.search(rf"\b{re.escape(name.lower())}\b", lowered):
            return db.get(models.Employee, emp_id)
        if re.search(rf"\b{re.escape(first)}\b", lowered) and (
            best is None or len(first) > best[1]
        ):
            best = (emp_id, len(first))
    if best:
        return db.get(models.Employee, best[0])
    return None


def _find_project(db: Session, text: str) -> Optional[models.Project]:
    lowered = text.lower()
    for proj in db.query(models.Project).all():
        if re.search(rf"\b{re.escape(proj.name.lower())}\b", lowered):
            return proj
    return None


def answer_query(db: Session, query: str) -> dict:
    text = query.strip()
    lowered = text.lower()

    # ---- Intent: available seats -------------------------------------------
    if "available" in lowered and "seat" in lowered:
        q = db.query(models.Seat).filter(models.Seat.status == "Available")
        floor_match = FLOOR_RE.search(lowered)
        floor = None
        if floor_match:
            floor = int(floor_match.group(1))
            q = q.filter(models.Seat.floor == floor)
        total = q.count()
        examples = q.limit(5).all()
        sample = ", ".join(s.seat_number for s in examples)
        where = f" on Floor {floor}" if floor else ""
        answer = (
            f"There are {total} available seats{where}."
            + (f" For example: {sample}." if sample else "")
        )
        return {
            "answer": answer,
            "intent": "available_seats",
            "data": {"count": total, "floor": floor},
        }

    # ---- Intent: seat utilization for a project ----------------------------
    if ("occupied" in lowered or "utilization" in lowered or "how many seats" in lowered):
        proj = _find_project(db, text)
        if proj:
            occupied = (
                db.query(func.count(models.SeatAllocation.id))
                .filter(
                    models.SeatAllocation.project_id == proj.id,
                    models.SeatAllocation.allocation_status == "Active",
                )
                .scalar()
            )
            emp_count = (
                db.query(func.count(models.Employee.id))
                .filter(models.Employee.project_id == proj.id)
                .scalar()
            )
            return {
                "answer": (
                    f"Project {proj.name} has {occupied} occupied seats across "
                    f"{emp_count} assigned employees."
                ),
                "intent": "project_utilization",
                "data": {"project": proj.name, "occupied": occupied, "employees": emp_count},
            }

    # ---- Intent: "who is sitting near me / near X" -------------------------
    if "near" in lowered and ("who" in lowered or "sitting" in lowered):
        emp = _find_employee(db, text)
        if emp:
            alloc = services.active_allocation(db, emp.id)
            if not alloc:
                return {
                    "answer": f"{emp.name} does not have a seat allocated yet, so I can't find neighbours.",
                    "intent": "neighbours",
                    "data": None,
                }
            seat = alloc.seat
            neighbours = (
                db.query(models.Seat)
                .join(
                    models.SeatAllocation,
                    (models.SeatAllocation.seat_id == models.Seat.id)
                    & (models.SeatAllocation.allocation_status == "Active"),
                )
                .filter(
                    models.Seat.floor == seat.floor,
                    models.Seat.zone == seat.zone,
                    models.Seat.bay == seat.bay,
                    models.Seat.id != seat.id,
                )
                .limit(6)
                .all()
            )
            names = []
            for s in neighbours:
                na = (
                    db.query(models.SeatAllocation)
                    .filter(
                        models.SeatAllocation.seat_id == s.id,
                        models.SeatAllocation.allocation_status == "Active",
                    )
                    .first()
                )
                if na:
                    names.append(f"{na.employee.name} ({s.seat_number})")
            if names:
                return {
                    "answer": f"Sitting near {emp.name} in Bay {seat.bay}: " + ", ".join(names) + ".",
                    "intent": "neighbours",
                    "data": {"neighbours": names},
                }
            return {
                "answer": f"{emp.name} currently has no seated neighbours in Bay {seat.bay}.",
                "intent": "neighbours",
                "data": None,
            }

    # ---- Intent: project assignment ----------------------------------------
    if "project" in lowered and ("which" in lowered or "assigned" in lowered or "my project" in lowered):
        emp = _find_employee(db, text)
        if emp:
            proj = emp.project.name if emp.project else "not assigned to any project"
            return {
                "answer": f"{emp.name} is assigned to Project {proj}."
                if emp.project
                else f"{emp.name} is not assigned to any project.",
                "intent": "project_assignment",
                "data": {"employee": emp.name, "project": emp.project.name if emp.project else None},
            }

    # ---- Intent: where is my/employee seat (default seat lookup) ------------
    if "seat" in lowered or "where" in lowered or "sit" in lowered or "seated" in lowered:
        emp = _find_employee(db, text)
        if emp:
            alloc = services.active_allocation(db, emp.id)
            if alloc:
                seat = alloc.seat
                proj = emp.project.name if emp.project else "no project"
                return {
                    "answer": (
                        f"{emp.name} is seated at {_seat_phrase(seat)}. "
                        f"Assigned project: {proj}."
                    ),
                    "intent": "seat_lookup",
                    "data": {
                        "employee": emp.name,
                        "seat": seat.seat_number,
                        "floor": seat.floor,
                        "zone": seat.zone,
                        "bay": seat.bay,
                        "project": emp.project.name if emp.project else None,
                    },
                }
            return {
                "answer": (
                    f"{emp.name} has not been allocated a seat yet. "
                    "Ask Admin/HR to run allocation for this new joiner."
                ),
                "intent": "seat_lookup",
                "data": {"employee": emp.name, "seat": None},
            }
        return {
            "answer": (
                "I couldn't identify the employee. Please include an email "
                "(e.g. 'amit@ethara.ai') or the full employee name."
            ),
            "intent": "seat_lookup",
            "data": None,
        }

    # ---- Fallback -----------------------------------------------------------
    return {
        "answer": (
            "I can help with seat locations, project assignments, available "
            "seats, team neighbours and seat utilization. Try: "
            "'Where is my seat? My email is amit@ethara.ai'."
        ),
        "intent": "unknown",
        "data": None,
    }
