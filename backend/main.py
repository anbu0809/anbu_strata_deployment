import os
import sys
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the parent directory to the path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use absolute imports since we're running the module directly
from backend.routes import connections, session, analyze, extract, migrate, validate
from backend.database import init_db

# Load environment variables from .env file
load_dotenv()

# Initialize the database
init_db()

app = FastAPI(title="Strata - Enterprise AI Translation Platform")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(connections.router, prefix="/api/connections", tags=["connections"])
app.include_router(session.router, prefix="/api/session", tags=["session"])
app.include_router(analyze.router, prefix="/api/analyze", tags=["analyze"])
app.include_router(extract.router, prefix="/api/extract", tags=["extract"])
app.include_router(migrate.router, prefix="/api/migrate", tags=["migrate"])
app.include_router(validate.router, prefix="/api/validate", tags=["validate"])

# Add global export routes for validation reports
from backend.routes.validate import router as validate_router
app.include_router(validate_router, prefix="/api", tags=["export"])

@app.get("/")
async def root():
    return {"message": "Strata - Enterprise AI Translation Platform"}

@app.get("/api/health")
async def health_check():
    return {"status": "online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
