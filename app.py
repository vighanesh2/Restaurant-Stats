from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import knot_route, orders_route
from app.mongo import mongo_client

# Create FastAPI app instance
fastapi_app = FastAPI(
    title="Restaurant Stats API",
    description="API for querying restaurant order data from MongoDB",
    version="1.0.0"
)

# CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
fastapi_app.include_router(knot_route.router, prefix="/api")
fastapi_app.include_router(orders_route.router, prefix="/api")
fastapi_app.include_router(mongo_client.router, prefix="/api")


@fastapi_app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Restaurant Stats API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@fastapi_app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# Export as 'app' for compatibility with uvicorn and deployment configs
app = fastapi_app

