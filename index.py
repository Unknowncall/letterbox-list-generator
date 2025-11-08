from contextlib import asynccontextmanager
from fastapi import FastAPI
from routers import users, jobs
from jobs.scheduler import init_scheduler, shutdown_scheduler
import atexit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    # Startup: Initialize services
    init_scheduler()
    yield
    # Shutdown: Cleanup services
    shutdown_scheduler()


app = FastAPI(
    title="Letterbox List Generator",
    lifespan=lifespan
)

# Include routers
app.include_router(users.router)
app.include_router(jobs.router)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Ensure cleanup on process exit
atexit.register(shutdown_scheduler)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
