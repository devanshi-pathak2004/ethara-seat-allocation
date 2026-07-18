"""Shared business logic: serialization helpers + seat allocation engine.

Keeping the allocation rules in one place means the REST endpoints and the
AI assistant both go through exactly the same, well-tested code path.
"""
from .utils import utcnow
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models


# --------------------------------------------------------------------------- #
#  Serialization helpers
# --------------------------------------------------------------------------- #
def active_allocation(db: Session, employee_id: int) -> Optional[models.SeatAllocation]:
    return (
        db.query(models.SeatAllocation)
        .filter(
            models.SeatAllocation.employee_id == employee_id,
            models.SeatAllocation.allocation_status == "Active",
        )
        .first()
    )


def serialize_employee(emp: models.Employee, db: Session) -> dict:
    alloc = active_allocation(db, emp.id)
    seat = alloc.seat if alloc else None
    return {
        "id": emp.id,
        "employee_code": emp.employee_code,
        "name": emp.name,
        "email": emp.email,
        "department": emp.department,
        "role": emp.role,
        "joining_date": emp.joining_date,
        "status": emp.status,
        "project_id": emp.project_id,
        "created_at": emp.created_at,
        "project_name": emp.project.name if emp.project else None,
        "allocation_status": "Allocated" if alloc else "Pending",
        "seat": {
            "id": seat.id,
            "floor": seat.floor,
            "zone": seat.zone,
            "bay": seat.bay,
            "seat_number": seat.seat_number,
            "status": seat.status,
        }
        if seat
        else None,
    }


def serialize_seat(seat: models.Seat, db: Session) -> dict:
    alloc = (
        db.query(models.SeatAllocation)
        .filter(
            models.SeatAllocation.seat_id == seat.id,
            models.SeatAllocation.allocation_status == "Active",
        )
        .first()
    )
    emp = alloc.employee if alloc else None
    return {
        "id": seat.id,
        "floor": seat.floor,
        "zone": seat.zone,
        "bay": seat.bay,
        "seat_number": seat.seat_number,
        "status": seat.status,
        "created_at": seat.created_at,
        "employee_name": emp.name if emp else None,
        "employee_id": emp.id if emp else None,
        "project_name": alloc.project.name if alloc and alloc.project else None,
    }


# --------------------------------------------------------------------------- #
#  Allocation engine
# --------------------------------------------------------------------------- #
class AllocationError(Exception):
    """Raised when a seat cannot be allocated / released."""


def suggest_seat(
    db: Session,
    project_id: Optional[int] = None,
    preferred_floor: Optional[int] = None,
    preferred_zone: Optional[str] = None,
) -> Optional[models.Seat]:
    """Suggest the best available seat, honouring team proximity.

    Priority order:
      1. Available seat on the preferred floor + zone.
      2. Available seat in a zone where the employee's project already sits
         (keeps teams together).
      3. Available seat on the preferred floor (any zone).
      4. Any available seat at all (alternate zone fallback).
    """
    base = db.query(models.Seat).filter(models.Seat.status == "Available")

    # 1. Exact preferred floor + zone.
    if preferred_floor and preferred_zone:
        seat = base.filter(
            models.Seat.floor == preferred_floor,
            models.Seat.zone == preferred_zone,
        ).first()
        if seat:
            return seat

    # 2. Cluster near the rest of the project team.
    if project_id:
        cluster = (
            db.query(models.Seat.floor, models.Seat.zone, func.count().label("cnt"))
            .join(
                models.SeatAllocation,
                (models.SeatAllocation.seat_id == models.Seat.id)
                & (models.SeatAllocation.allocation_status == "Active"),
            )
            .filter(models.SeatAllocation.project_id == project_id)
            .group_by(models.Seat.floor, models.Seat.zone)
            .order_by(func.count().desc())
            .all()
        )
        for floor, zone, _cnt in cluster:
            seat = base.filter(
                models.Seat.floor == floor, models.Seat.zone == zone
            ).first()
            if seat:
                return seat

    # 3. Preferred floor, any zone.
    if preferred_floor:
        seat = base.filter(models.Seat.floor == preferred_floor).first()
        if seat:
            return seat

    # 4. Any available seat.
    return base.order_by(models.Seat.floor, models.Seat.zone).first()


def allocate_seat(
    db: Session,
    employee_id: int,
    seat_id: Optional[int] = None,
    preferred_floor: Optional[int] = None,
    preferred_zone: Optional[str] = None,
) -> models.SeatAllocation:
    emp = db.get(models.Employee, employee_id)
    if not emp:
        raise AllocationError("Employee not found.")

    # Rule: one employee -> one active seat.
    if active_allocation(db, employee_id):
        raise AllocationError(
            f"{emp.name} already has an active seat. Release it before re-allocating."
        )

    if seat_id:
        seat = db.get(models.Seat, seat_id)
        if not seat:
            raise AllocationError("Seat not found.")
    else:
        seat = suggest_seat(db, emp.project_id, preferred_floor, preferred_zone)
        if not seat:
            raise AllocationError("No available seats to allocate.")

    # Rule: reserved / maintenance / occupied seats are not allocatable.
    if seat.status != "Available":
        raise AllocationError(
            f"Seat {seat.seat_number} is '{seat.status}' and cannot be allocated."
        )

    # Rule: one seat -> one active employee (guards against races).
    existing = (
        db.query(models.SeatAllocation)
        .filter(
            models.SeatAllocation.seat_id == seat.id,
            models.SeatAllocation.allocation_status == "Active",
        )
        .first()
    )
    if existing:
        raise AllocationError(f"Seat {seat.seat_number} is already occupied.")

    seat.status = "Occupied"
    allocation = models.SeatAllocation(
        employee_id=emp.id,
        seat_id=seat.id,
        project_id=emp.project_id,
        allocation_status="Active",
        allocation_date=utcnow(),
    )
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    return allocation


def release_seat(
    db: Session,
    seat_id: Optional[int] = None,
    employee_id: Optional[int] = None,
) -> models.SeatAllocation:
    q = db.query(models.SeatAllocation).filter(
        models.SeatAllocation.allocation_status == "Active"
    )
    if seat_id:
        q = q.filter(models.SeatAllocation.seat_id == seat_id)
    if employee_id:
        q = q.filter(models.SeatAllocation.employee_id == employee_id)

    allocation = q.first()
    if not allocation:
        raise AllocationError("No active allocation found for the given seat/employee.")

    allocation.allocation_status = "Released"
    allocation.released_date = utcnow()
    # Released seats become available again.
    allocation.seat.status = "Available"
    db.commit()
    db.refresh(allocation)
    return allocation
