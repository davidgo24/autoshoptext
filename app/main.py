from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from app.routes.vin import create_new_vin as vin_create
from app.routes.vin import get_vin_profile as vin_read
from app.routes.service_record import create_service_record as sr_create
from app.routes.decode_vin import decode_vin_nhtsa
from app.routes.contact import contact as contact_routes
from app.core.database import init_db
from app.core.scheduler import start_scheduler
from fastapi.staticfiles import StaticFiles
import os
import asyncio



app = FastAPI()

app.include_router(vin_create.router, prefix="/vin", tags=["VIN"])
app.include_router(vin_read.router, prefix="/vin", tags=["VIN"])
app.include_router(sr_create.router, prefix="/service-record", tags=["ServiceRecord"])
app.include_router(decode_vin_nhtsa.router, prefix="/vin", tags=["VIN Decode"])
app.include_router(contact_routes.router, prefix="/contacts", tags=["Contacts"])
app.mount(
    "/", 
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static"), html=True), 
    name="static"
)
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