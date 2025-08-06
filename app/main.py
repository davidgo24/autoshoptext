from fastapi import FastAPI
from app.routes.vin import create_new_vin as vin_create
from app.routes.vin import get_vin_profile as vin_read
from app.routes.service_record import create_service_record as sr_create

app = FastAPI()

app.include_router(vin_create.router, prefix="/vin", tags=["VIN"])
app.include_router(vin_read.router, prefix="/vin", tags=["VIN"])
app.include_router(sr_create.router, prefix="/service-record", tags=["ServiceRecord"])
