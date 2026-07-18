"""Ethara Seat Allocation & Project Mapping System — FastAPI entrypoint."""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import ai, dashboard, employees, projects, seats

# Create tables on startup (safe no-op if they already exist).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Ethara Seat Allocation & Project Mapping System",
    description=(
        "Centralised API to manage seating, project mapping, floor allocation "
        "and joining updates for ~5,000 Ethara employees. Includes a natural-"
        "language AI assistant for seat & project queries."
    ),
    version="1.0.0",
)

# CORS — allow the React frontend (and any deployed origin) to call the API.
# Note: the CORS spec forbids combining a wildcard origin ("*") with
# allow_credentials=True — browsers then drop the Access-Control-Allow-Origin
# header and block the request. So we only enable credentials when explicit
# origins are configured; with "*" we disable credentials (we don't use cookies).
origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
if not origins:  # blank / misconfigured env var -> allow all (don't break the app)
    origins = ["*"]
allow_credentials = "*" not in origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(employees.router)
app.include_router(projects.router)
app.include_router(seats.router)
app.include_router(dashboard.router)
app.include_router(ai.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Ethara Seat Allocation & Project Mapping System",
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
