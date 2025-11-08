from main import app

# Export the FastAPI app for Vercel
# Vercel will automatically handle the ASGI application
__all__ = ["app"]

