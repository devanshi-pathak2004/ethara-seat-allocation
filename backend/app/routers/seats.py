"""Seat management + allocation endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas, services
from ..database import get_db

router = APIRouter(prefix="/seats", tags=["Seats"])


@router.post("", response_model=schemas.SeatOut, status_code=201)
def create_seat(payload: schemas.SeatCreate, db: Session = Depends(get_db)):
    # Rule: no duplicate seat number on the same floor/zone.
    dup = (
        db.query(models.Seat)
        .filter(
            models.Seat.floor == payload.floor,
            models.Seat.zone == payload.zone,
            models.Seat.seat_number == payload.seat_number,
        )
        .first()
    )
    if dup:
        raise HTTPException(
            status_code=409,
            detail="Seat number already exists on this floor/zone.",
        )
    seat = models.Seat(**payload.model_dump())
    db.add(seat)
    db.commit()
    db.refresh(seat)
    return services.serialize_seat(seat, db)


@router.get("", response_model=schemas.SeatList)
def list_seats(
    db: Session = Depends(get_db),
    floor: Optional[int] = None,
    zone: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = Query(None, description="Match seat number"),
    limit: int = Query(100, le=1000),
    offset: int = 0,
):
    q = db.query(models.Seat)
    if floor:
        q = q.filter(models.Seat.floor == floor)
    if zone:
        q = q.filter(models.Seat.zone == zone)
    if status:
        q = q.filter(models.Seat.status == status)
    if search:
        q = q.filter(models.Seat.seat_number.ilike(f"%{search}%"))
    total = q.count()
    rows = (
        q.order_by(models.Seat.floor, models.Seat.zone, models.Seat.seat_number)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": [services.serialize_seat(s, db) for s in rows]}


@router.get("/available", response_model=schemas.SeatList)
def available_seats(
    db: Session = Depends(get_db),
    floor: Optional[int] = None,
    zone: Optional[str] = None,
    limit: int = Query(100, le=1000),
):
    q = db.query(models.Seat).filter(models.Seat.status == "Available")
    if floor:
        q = q.filter(models.Seat.floor == floor)
    if zone:
        q = q.filter(models.Seat.zone == zone)
    total = q.count()
    rows = q.order_by(models.Seat.floor, models.Seat.zone).limit(limit).all()
    return {"total": total, "items": [services.serialize_seat(s, db) for s in rows]}


@router.post("/allocate")
def allocate(payload: schemas.AllocateRequest, db: Session = Depends(get_db)):
    try:
        allocation = services.allocate_seat(
            db,
            employee_id=payload.employee_id,
            seat_id=payload.seat_id,
            preferred_floor=payload.preferred_floor,
            preferred_zone=payload.preferred_zone,
        )
    except services.AllocationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "message": "Seat allocated successfully.",
        "allocation_id": allocation.id,
        "employee": services.serialize_employee(allocation.employee, db),
        "seat": services.serialize_seat(allocation.seat, db),
    }


@router.post("/release")
def release(payload: schemas.ReleaseRequest, db: Session = Depends(get_db)):
    if not payload.seat_id and not payload.employee_id:
        raise HTTPException(status_code=400, detail="Provide seat_id or employee_id.")
    try:
        allocation = services.release_seat(
            db, seat_id=payload.seat_id, employee_id=payload.employee_id
        )
    except services.AllocationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {
        "message": "Seat released. It is now available again.",
        "seat": services.serialize_seat(allocation.seat, db),
    }
