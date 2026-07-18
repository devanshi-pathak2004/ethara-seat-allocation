"""Seed the database only if it is currently empty.

Used by the Docker/Render start command so that a container restart does not
wipe existing data, while a brand-new deployment still gets demo data.
"""
from .database import Base, SessionLocal, engine
from . import models


def run():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        has_data = db.query(models.Employee).first() is not None
    finally:
        db.close()

    if has_data:
        print("Database already seeded — skipping.")
        return

    print("Empty database detected — seeding demo data…")
    from .seed import seed

    seed()


if __name__ == "__main__":
    run()
