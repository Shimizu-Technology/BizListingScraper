"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .routers import listings, stats
from .database import init_pool, close_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    # Startup
    init_pool()
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
        # Add your production frontend URL here
        # "https://your-frontend.vercel.app",
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
