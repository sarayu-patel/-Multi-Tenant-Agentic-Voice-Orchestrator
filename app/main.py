from contextlib import asynccontextmanager
import os
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import connect, disconnect
from app.database.seed import run_seed
from app.routers import companies, leads, campaigns, webhooks


# Lifecycle: connect to MongoDB on startup, seed if empty, disconnect on shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect()
    # startup: open DB connection
    await run_seed()       # startup: fill DB if empty
    yield                  # <-- server runs here, serving requests
    await disconnect()     # shutdown: close DB connection


app = FastAPI(
    title="Voice Agent API",
    description="Multi-tenant outbound calling system powered by Vapi + LangGraph",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the frontend (any origin during dev) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all route groups
app.include_router(companies.router)
app.include_router(leads.router)
app.include_router(campaigns.router)
app.include_router(webhooks.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")