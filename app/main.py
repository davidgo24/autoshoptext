from fastapi import FastAPI, Request, Depends, HTTPException, APIRouter
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os

from app.routes.vin import create_new_vin as vin_create
from app.routes.vin import get_vin_profile as vin_read
from app.routes.service_record import create_service_record as sr_create
from app.routes.service_record import read_service_record as sr_read
from app.routes.decode_vin import decode_vin_nhtsa
from app.routes.contact import contact as contact_routes
from app.routes.message import send_message as message_routes
from app.routes.message import inbound as inbound_routes
from app.routes.message import cost_tracking as cost_routes
from app.core.database import init_db
from app.core.scheduler import start_scheduler
from app.core.security import get_current_username # Keep this import for now, will adjust later
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncio

app = FastAPI()

# Templates for serving HTML
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "static"))

# --- Multi-tenant Basic Auth Logic ---
TENANT_CREDENTIALS = {
    "montebello": os.getenv("SHOP_PASSWORD_MONTEBELLO", "mblnt25"),
    "eastlube": os.getenv("SHOP_PASSWORD_EASTLUBE", "eastlube456")
}

def get_current_user(credentials: HTTPBasicCredentials = Depends(HTTPBasic())):
    correct_password = TENANT_CREDENTIALS.get(credentials.username)
    if not correct_password or not secrets.compare_digest(credentials.password.encode('utf-8'), correct_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials.username

# --- Routing ---

# Unprotected webhook for Twilio
app.include_router(inbound_routes.router, tags=["Messages"])

# Protected API routes
protected_router = APIRouter(dependencies=[Depends(get_current_user)])
protected_router.include_router(vin_create.router, prefix="/vin", tags=["VIN"])
protected_router.include_router(vin_read.router, prefix="/vin", tags=["VIN"])
protected_router.include_router(sr_create.router, prefix="/service-record", tags=["ServiceRecord"])
protected_router.include_router(sr_read.router, prefix="/service-record", tags=["ServiceRecord"])
protected_router.include_router(decode_vin_nhtsa.router, prefix="/vin", tags=["VIN Decode"])
protected_router.include_router(contact_routes.router, prefix="/contacts", tags=["Contacts"])
protected_router.include_router(message_routes.router, prefix="/messages", tags=["Messages"])
protected_router.include_router(cost_routes.router, prefix="/messages", tags=["Costs"])

@protected_router.get("/vin/test-auth")
async def test_auth():
    return {"message": "Authentication successful!"}

@protected_router.get("/protected-test")
async def protected_test():
    return {"message": "Authentication successful!"}

# Include the protected router into the main app
app.include_router(protected_router)

import os

# Publicly accessible login page
@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "login.html"))

# Main application page (authentication handled by JavaScript)
@app.get("/app", response_class=HTMLResponse)
async def main_app(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Publicly accessible static files (for login.html and its JS/CSS)
app.mount(
    "/static", 
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), 
    name="static"
)

# --- Startup/Shutdown Events ---
@app.on_event("startup")
async def on_startup():
    print("Running DB init...")
    await init_db()
    print("DB init done")
    asyncio.create_task(start_scheduler()) # Start the background scheduler

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )