"""Seed the database with realistic demo data.

Targets (all satisfied by the numbers below):
  * 5,000 employees
  * 6,000 seats  (>= 5,500)  across 5 floors x 4 zones (20 zones >= 10)
  * 11 projects  (>= 10)
  * >= 500 available seats
  * >= 100 reserved seats
  * ~50 employees pending allocation

Run:  python -m app.seed          (from the backend/ directory)
"""
import random
from datetime import date, timedelta
from .utils import utcnow

from .database import Base, SessionLocal, engine
from . import models

random.seed(42)  # reproducible dataset

PROJECT_NAMES = [
    "Indigo", "Indreed", "Mydreed", "Preed", "Serfy", "Oreed",
    "bedegreed", "Opreed", "Serry", "Kaary", "Mered",
]

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Data Science", "QA",
    "DevOps", "HR", "Finance", "Growth", "Support",
]
ROLES = [
    "Software Engineer", "Senior Engineer", "Tech Lead", "Product Manager",
    "UX Designer", "Data Analyst", "QA Engineer", "DevOps Engineer",
    "Scrum Master", "Associate", "Manager", "Intern",
]
MANAGERS = [
    "Sarah Khan", "Rahul Verma", "Aisha Patel", "David Chen", "Maria Lopez",
    "Omar Farouk", "Priya Nair", "James Wright", "Lena Müller", "Ahmed Ali",
    "Nina Roy",
]

FIRST_NAMES = [
    "Amit", "Priya", "Rahul", "Sara", "John", "Aisha", "David", "Maria",
    "Omar", "Nina", "Leo", "Fatima", "Chen", "Yuki", "Carlos", "Emma",
    "Noah", "Zara", "Ivan", "Mei", "Raj", "Sofia", "Hassan", "Grace",
    "Arjun", "Lucia", "Kenji", "Anna", "Vikram", "Elena", "Sam", "Layla",
    "Tariq", "Isla", "Marco", "Divya", "Peter", "Hana", "Ali", "Ria",
]
LAST_NAMES = [
    "Sharma", "Khan", "Patel", "Chen", "Lopez", "Farouk", "Nair", "Wright",
    "Müller", "Ali", "Roy", "Singh", "Kumar", "Gupta", "Reddy", "Das",
    "Bose", "Iyer", "Mehta", "Joshi", "Verma", "Rao", "Nguyen", "Kim",
    "Sato", "Costa", "Silva", "Rossi", "Ivanov", "Novak", "Haddad", "Aziz",
]

FLOORS = [1, 2, 3, 4, 5]
ZONES = ["A", "B", "C", "D"]
BAYS_PER_ZONE = 12
SEATS_PER_BAY = 25
# => 5 * 4 * 12 * 25 = 6,000 seats


def wipe():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed():
    wipe()
    db = SessionLocal()
    try:
        # ---- Projects ------------------------------------------------------
        projects = []
        for i, name in enumerate(PROJECT_NAMES):
            projects.append(
                models.Project(
                    name=name,
                    description=f"{name} initiative at Ethara.",
                    manager_name=MANAGERS[i % len(MANAGERS)],
                    status="Active",
                )
            )
        db.add_all(projects)
        db.commit()
        project_ids = [p.id for p in db.query(models.Project).all()]
        print(f"✓ {len(project_ids)} projects")

        # ---- Seats ---------------------------------------------------------
        seats = []
        for floor in FLOORS:
            for zone in ZONES:
                for bay in range(1, BAYS_PER_ZONE + 1):
                    for n in range(1, SEATS_PER_BAY + 1):
                        seats.append(
                            models.Seat(
                                floor=floor,
                                zone=zone,
                                bay=bay,
                                seat_number=f"{zone}{bay}-{n:02d}",
                                status="Available",
                            )
                        )
        db.bulk_save_objects(seats)
        db.commit()
        seat_rows = db.query(models.Seat).all()
        print(f"✓ {len(seat_rows)} seats")

        # ---- Employees -----------------------------------------------------
        employees = []
        used_emails = set()
        for i in range(1, 5001):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            base_email = f"{fn.lower()}.{ln.lower()}"
            email = f"{base_email}@ethara.ai"
            if email in used_emails:
                email = f"{base_email}{i}@ethara.ai"
            used_emails.add(email)
            joining = date(2024, 1, 1) + timedelta(days=random.randint(0, 700))
            employees.append(
                models.Employee(
                    employee_code=f"ETH{i:05d}",
                    name=f"{fn} {ln}",
                    email=email,
                    department=random.choice(DEPARTMENTS),
                    role=random.choice(ROLES),
                    joining_date=joining,
                    status="Active",
                    project_id=random.choice(project_ids),
                )
            )
        db.bulk_save_objects(employees)
        db.commit()
        emp_rows = db.query(models.Employee).order_by(models.Employee.id).all()
        print(f"✓ {len(emp_rows)} employees")

        # Guarantee a well-known demo employee for screenshots / testing.
        demo = emp_rows[0]
        demo.name = "Amit Sharma"
        demo.email = "amit@ethara.ai"
        demo.department = "Engineering"
        demo.role = "Software Engineer"
        db.commit()

        # ---- Reserve / maintenance seats before allocating -----------------
        random.shuffle(seat_rows)
        reserved = seat_rows[:150]
        maintenance = seat_rows[150:250]
        for s in reserved:
            s.status = "Reserved"
        for s in maintenance:
            s.status = "Maintenance"
        db.commit()

        allocatable = seat_rows[250:]  # remaining are Available

        # ---- Allocations: 4,950 employees seated, ~50 pending --------------
        # Cluster by project so team-proximity queries look realistic:
        # sort allocatable seats by (floor, zone, bay) and assign employees
        # grouped by project into contiguous blocks.
        allocatable.sort(key=lambda s: (s.floor, s.zone, s.bay, s.seat_number))
        emps_to_seat = emp_rows[:4950]
        emps_to_seat.sort(key=lambda e: (e.project_id, e.id))

        # Leave ~800 available seats spread EVENLY across all floors/zones
        # (rather than bunched on the top floor) so demo queries like
        # "available seats on Floor 3" return realistic results.
        target_gaps = len(allocatable) - len(emps_to_seat)  # 800
        gap_step = len(allocatable) / target_gaps
        seats_for_alloc, next_gap, gaps_left = [], gap_step, target_gaps
        for i, s in enumerate(allocatable):
            if gaps_left > 0 and i >= next_gap:
                gaps_left -= 1
                next_gap += gap_step
                continue  # leave this seat Available
            seats_for_alloc.append(s)
        seats_for_alloc = seats_for_alloc[: len(emps_to_seat)]

        allocations = []
        for emp, seat in zip(emps_to_seat, seats_for_alloc):
            seat.status = "Occupied"
            allocations.append(
                models.SeatAllocation(
                    employee_id=emp.id,
                    seat_id=seat.id,
                    project_id=emp.project_id,
                    allocation_status="Active",
                    allocation_date=utcnow(),
                )
            )
        db.bulk_save_objects(allocations)
        db.commit()

        # ---- Report --------------------------------------------------------
        from sqlalchemy import func

        def seat_count(status):
            return (
                db.query(func.count(models.Seat.id))
                .filter(models.Seat.status == status)
                .scalar()
            )

        print("\n─── Seed summary ─────────────────────────────")
        print(f"Employees          : {db.query(func.count(models.Employee.id)).scalar()}")
        print(f"Projects           : {len(project_ids)}")
        print(f"Seats total        : {db.query(func.count(models.Seat.id)).scalar()}")
        print(f"  Occupied         : {seat_count('Occupied')}")
        print(f"  Available        : {seat_count('Available')}")
        print(f"  Reserved         : {seat_count('Reserved')}")
        print(f"  Maintenance      : {seat_count('Maintenance')}")
        print(f"Pending allocation : {len(emp_rows) - len(emps_to_seat)}")
        print(f"Demo login employee: {demo.email}")
        print("──────────────────────────────────────────────")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
