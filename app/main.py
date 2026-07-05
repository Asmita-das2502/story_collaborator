from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import create_tables
from app.routers import chat , summary, chapters


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up — creating tables if needed...")
    await create_tables()
    print("✅ Database ready.")
    yield
    print("Shutting down.")


app = FastAPI(
    title="Story Collaborator",
    description="A collaborative story writing tool with Cognee-powered memory",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(chat.router)
app.include_router(summary.router)
app.include_router(chapters.router)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "Story Collaborator"}