from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.knot_route import router as knot_router
from services.mock_data import MOCK_ORDER_DATA

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


@app.get("/playground")
async def playground():
    return FileResponse("playground.html")


@app.get("/mock-order")
async def mock_order():
    return MOCK_ORDER_DATA


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
