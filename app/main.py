from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import create_tables
from app.routers import chat , summary, chapters


# ─────────────────────────────────────────────
# Lifespan: runs once at startup and shutdown
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables if they don't exist yet
    print("Starting up — creating tables if needed...")
    await create_tables()
    print("✅ Database ready.")
    yield
    # Shutdown: nothing to clean up for now
    print("Shutting down.")


# ─────────────────────────────────────────────
# App instance
# ─────────────────────────────────────────────
app = FastAPI(
    title="Story Collaborator",
    description="A collaborative story writing tool with Cognee-powered memory",
    version="1.0.0",
    lifespan=lifespan
)


# ─────────────────────────────────────────────
# Register routers
# ─────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(summary.router)
app.include_router(chapters.router)


# ─────────────────────────────────────────────
# Serve static files (your HTML/JS/CSS frontend)
# ─────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─────────────────────────────────────────────
# Root: serve the main HTML page
# ─────────────────────────────────────────────
@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


# ─────────────────────────────────────────────
# Health check — useful for verifying the app
# is running during dev and for deployment later
# ─────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "Story Collaborator"}