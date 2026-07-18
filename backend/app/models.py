"""SQLAlchemy ORM models.

The schema mirrors the four tables described in the assessment brief:
employees, projects, seats and seat_allocations.
"""
from datetime import date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from .database import Base
from .utils import utcnow


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String, default="")
    manager_name = Column(String, default="")
    status = Column(String, default="Active")  # Active / Inactive
    created_at = Column(DateTime, default=utcnow)

    employees = relationship("Employee", back_populates="project")
    allocations = relationship("SeatAllocation", back_populates="project")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, default="")
    role = Column(String, default="")
    joining_date = Column(Date, default=date.today)
    status = Column(String, default="Active")  # Active / Inactive
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    project = relationship("Project", back_populates="employees")
    allocations = relationship("SeatAllocation", back_populates="employee")


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    floor = Column(Integer, nullable=False, index=True)
    zone = Column(String, nullable=False, index=True)
    bay = Column(Integer, nullable=False)
    seat_number = Column(String, nullable=False, index=True)
    status = Column(String, default="Available", index=True)  # Available/Occupied/Reserved/Maintenance
    created_at = Column(DateTime, default=utcnow)

    allocations = relationship("SeatAllocation", back_populates="seat")

    # Business rule: no duplicate seat number on the same floor/zone.
    __table_args__ = (
        UniqueConstraint("floor", "zone", "seat_number", name="uq_seat_location"),
        Index("ix_seat_floor_zone", "floor", "zone"),
    )


class SeatAllocation(Base):
    __tablename__ = "seat_allocations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    allocation_status = Column(String, default="Active", index=True)  # Active / Released
    allocation_date = Column(DateTime, default=utcnow)
    released_date = Column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="allocations")
    seat = relationship("Seat", back_populates="allocations")
    project = relationship("Project", back_populates="allocations")
