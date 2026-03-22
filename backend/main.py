import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Verify required API keys are loaded
if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError(
        "GOOGLE_API_KEY not found in environment variables. "
        "Please set it in your .env file or as an environment variable."
    )

from routes.analyze import router as analyze_router
from middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

logger.info("✓ Environment variables loaded successfully")
logger.info(f"✓ GOOGLE_API_KEY found (length: {len(os.getenv('GOOGLE_API_KEY', ''))})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Legislative Analyzer API starting up")
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Legislative Analyzer",
    description="Helps citizens understand Indian laws and parliamentary bills",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=10)

app.include_router(analyze_router, prefix="/api")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error. Please try again."})


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
