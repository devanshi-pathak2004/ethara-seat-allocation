"""Dashboard aggregation endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total_employees = db.query(func.count(models.Employee.id)).scalar()
    active_employees = (
        db.query(func.count(models.Employee.id))
        .filter(models.Employee.status == "Active")
        .scalar()
    )
    total_seats = db.query(func.count(models.Seat.id)).scalar()

    status_rows = (
        db.query(models.Seat.status, func.count(models.Seat.id))
        .group_by(models.Seat.status)
        .all()
    )
    status_counts = {status: count for status, count in status_rows}

    # Pending = active employee without an active seat allocation.
    allocated_emp_ids = select(models.SeatAllocation.employee_id).where(
        models.SeatAllocation.allocation_status == "Active"
    )
    pending = (
        db.query(func.count(models.Employee.id))
        .filter(
            models.Employee.status == "Active",
            ~models.Employee.id.in_(allocated_emp_ids),
        )
        .scalar()
    )

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_seats": total_seats,
        "occupied_seats": status_counts.get("Occupied", 0),
        "available_seats": status_counts.get("Available", 0),
        "reserved_seats": status_counts.get("Reserved", 0),
        "maintenance_seats": status_counts.get("Maintenance", 0),
        "pending_allocation": pending,
        "utilization_pct": round(
            (status_counts.get("Occupied", 0) / total_seats * 100), 1
        )
        if total_seats
        else 0,
    }


@router.get("/project-utilization")
def project_utilization(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Project.id,
            models.Project.name,
            func.count(models.Employee.id),
        )
        .outerjoin(models.Employee, models.Employee.project_id == models.Project.id)
        .group_by(models.Project.id, models.Project.name)
        .order_by(func.count(models.Employee.id).desc())
        .all()
    )

    # Active seat count per project.
    seat_rows = (
        db.query(models.SeatAllocation.project_id, func.count(models.SeatAllocation.id))
        .filter(models.SeatAllocation.allocation_status == "Active")
        .group_by(models.SeatAllocation.project_id)
        .all()
    )
    seats_by_project = {pid: cnt for pid, cnt in seat_rows}

    return [
        {
            "project_id": pid,
            "project": name,
            "employees": emp_count,
            "allocated_seats": seats_by_project.get(pid, 0),
        }
        for pid, name, emp_count in rows
    ]


@router.get("/floor-utilization")
def floor_utilization(db: Session = Depends(get_db)):
    rows = (
        db.query(
            models.Seat.floor,
            models.Seat.status,
            func.count(models.Seat.id),
        )
        .group_by(models.Seat.floor, models.Seat.status)
        .all()
    )
    floors: dict[int, dict] = {}
    for floor, status, count in rows:
        f = floors.setdefault(
            floor,
            {
                "floor": floor,
                "total": 0,
                "Occupied": 0,
                "Available": 0,
                "Reserved": 0,
                "Maintenance": 0,
            },
        )
        f[status] = count
        f["total"] += count

    result = []
    for f in sorted(floors.values(), key=lambda x: x["floor"]):
        f["occupancy_pct"] = (
            round(f["Occupied"] / f["total"] * 100, 1) if f["total"] else 0
        )
        result.append(f)
    return result
