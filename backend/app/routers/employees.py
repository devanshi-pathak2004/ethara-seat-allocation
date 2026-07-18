"""Employee CRUD + search/filter endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from .. import models, schemas, services
from ..database import get_db

router = APIRouter(prefix="/employees", tags=["Employees"])


def _next_employee_code(db: Session) -> str:
    last = db.query(models.Employee).order_by(models.Employee.id.desc()).first()
    n = (last.id + 1) if last else 1
    return f"ETH{n:05d}"


@router.post("", response_model=schemas.EmployeeOut, status_code=201)
def create_employee(payload: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    # Rule: duplicate email not allowed.
    if db.query(models.Employee).filter(models.Employee.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Employee email already exists.")

    if payload.project_id and not db.get(models.Project, payload.project_id):
        raise HTTPException(status_code=400, detail="Project does not exist.")

    emp = models.Employee(
        employee_code=payload.employee_code or _next_employee_code(db),
        name=payload.name,
        email=payload.email,
        department=payload.department or "",
        role=payload.role or "",
        joining_date=payload.joining_date,
        status=payload.status or "Active",
        project_id=payload.project_id,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return services.serialize_employee(emp, db)


@router.get("", response_model=schemas.EmployeeList)
def list_employees(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Match name / code / email"),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    allocation_status: Optional[str] = Query(None, description="Allocated / Pending"),
    limit: int = Query(50, le=500),
    offset: int = 0,
):
    q = db.query(models.Employee)
    if search:
        like = f"%{search}%"
        q = q.filter(
            or_(
                models.Employee.name.ilike(like),
                models.Employee.email.ilike(like),
                models.Employee.employee_code.ilike(like),
            )
        )
    if project_id:
        q = q.filter(models.Employee.project_id == project_id)
    if status:
        q = q.filter(models.Employee.status == status)

    # Filter on derived allocation status at the DB level so pagination stays
    # correct (an employee is "Allocated" iff they have an active allocation).
    if allocation_status:
        allocated_ids = select(models.SeatAllocation.employee_id).where(
            models.SeatAllocation.allocation_status == "Active"
        )
        if allocation_status.lower() == "allocated":
            q = q.filter(models.Employee.id.in_(allocated_ids))
        elif allocation_status.lower() == "pending":
            q = q.filter(~models.Employee.id.in_(allocated_ids))

    total = q.count()
    rows = q.order_by(models.Employee.id).offset(offset).limit(limit).all()
    items = [services.serialize_employee(e, db) for e in rows]
    return {"total": total, "items": items}


@router.get("/{employee_id}", response_model=schemas.EmployeeOut)
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.get(models.Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
    return services.serialize_employee(emp, db)


@router.put("/{employee_id}", response_model=schemas.EmployeeOut)
def update_employee(
    employee_id: int, payload: schemas.EmployeeUpdate, db: Session = Depends(get_db)
):
    emp = db.get(models.Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")

    data = payload.model_dump(exclude_unset=True)
    if "email" in data:
        dup = (
            db.query(models.Employee)
            .filter(models.Employee.email == data["email"], models.Employee.id != employee_id)
            .first()
        )
        if dup:
            raise HTTPException(status_code=409, detail="Email already in use.")
    for field, value in data.items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return services.serialize_employee(emp, db)


@router.delete("/{employee_id}", response_model=schemas.EmployeeOut)
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    """Soft-delete: mark inactive and release any held seat."""
    emp = db.get(models.Employee, employee_id)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found.")
    emp.status = "Inactive"
    alloc = services.active_allocation(db, emp.id)
    if alloc:
        services.release_seat(db, employee_id=emp.id)
    db.commit()
    db.refresh(emp)
    return services.serialize_employee(emp, db)
