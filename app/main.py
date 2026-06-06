from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.db.database import init_db, close_db
from app.api.routes import auth, teams, backlog, sprints

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events."""
    # Startup
    print("Starting up...")
    await init_db()
    yield
    # Shutdown
    print("Shutting down...")
    await close_db()

app = FastAPI(
    title="Backlog Tracking API",
    description="Multi-tenant backlog tracking for agile teams",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - configure for your frontend in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else ["https://frontend.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy", "environment": settings.app_env}

# Register routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(teams.router, prefix="/api/teams", tags=["Teams"])
app.include_router(backlog.router, prefix="/api/backlog", tags=["Backlog Items"])
app.include_router(sprints.router, prefix="/api/sprints", tags=["Sprints"])