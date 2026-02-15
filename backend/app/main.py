from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .middleware.correlation import CorrelationMiddleware
from .core.logger import logger
from .core.globals import init_globals

# Create FastAPI app
app = FastAPI(
    title="PS Backend",
    description="Backend API for PS Application",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationMiddleware)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    init_globals()
    logger.info("Global services initialized successfully", "main")



# Import and include routers
from .routers import chat
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

