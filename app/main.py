# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging

from app.database import engine
from app.routers import auth, transactions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LedgerApp_v2",
    description="Personal and family expense tracking with comprehensive financial analytics",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    logger.info("🚀 LedgerApp_v2 is starting up...")


@app.on_event("shutdown")
async def shutdown():
    logger.info("👋 LedgerApp_v2 is shutting down...")
    if engine:
        await engine.dispose()


@app.get("/")
async def root():
    return {
        "app": "LedgerApp_v2",
        "status": "running",
        "version": "1.0.0",
        "message": "Personal Finance Tracker API",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}


# Serve login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# Serve auth success page (for OAuth callback)
@app.get("/auth/success", response_class=HTMLResponse)
async def auth_success(request: Request, token: str = None):
    return templates.TemplateResponse(
        "auth_success.html", {"request": request, "token": token}
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request):
    return templates.TemplateResponse("transactions.html", {"request": request})


@app.get("/auth_callback", response_class=HTMLResponse)
async def auth_callback(request: Request):
    """Google OAuth callback page."""
    return templates.TemplateResponse("auth_callback.html", {"request": request})


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(
    transactions.router, prefix="/api/transactions", tags=["Transactions"]
)
