from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.knot_route import router as knot_router

app = FastAPI(title="Restaurant Stats API")
app.include_router(knot_router, prefix="/api/knot")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Restaurant Stats API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
