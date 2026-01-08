"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import listings, stats
from .database import init_pool, close_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup - initialize pool and warm up connection
    init_pool()
    
    # Warm up the connection to prevent first-request failures
    try:
        from .database import get_connection
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        print("[STARTUP] Database connection warmed up successfully")
    except Exception as e:
        print(f"[STARTUP] Database warm-up failed (will retry on first request): {e}")
    
    yield
    # Shutdown
    close_pool()

app = FastAPI(
    title="BizListingScraper API",
    description="API for browsing scraped business listings",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev
        "http://localhost:3000",  # React dev
        "https://biz-scraper.netlify.app",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(listings.router, prefix="/api/listings", tags=["Listings"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "BizListingScraper API",
        "version": "1.0.0",
        "docs": "/docs"
    }
