from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date
from enum import Enum

class OilType(str, Enum):
    SYNTHETIC = "SYNTHETIC"
    SYNTHETIC_BLEND = "SYNTHETIC_BLEND"
    FULL_SYNTHETIC = "FULL_SYNTHETIC"
    HIGH_MILEAGE_SYNTHETIC_BLEND = "HIGH_MILEAGE_SYNTHETIC_BLEND"
    HIGH_MILEAGE_FULL_SYNTHETIC = "HIGH_MILEAGE_FULL_SYNTHETIC"

class OilViscosity(str, Enum):
    W0_16 = "0W-16"
    W0_20 = "0W-20"
    W0_30 = "0W-30"
    W0_40 = "0W-40"
    W5_20 = "5W-20"
    W5_30 = "5W-30"
    W5_40 = "5W-40"
    W5_50 = "5W-50"
    W10_30 = "10W-30"
    W10_40 = "10W-40"
    W10_50 = "10W-50"
    W10_60 = "10W-60"
    W15_40 = "15W-40"
    W20_50 = "20W-50"
    W25_60 = "25W-60"

class ServiceRecordCreate(BaseModel):
    vin: str
    service_date: Optional[date] = None
    oil_type: OilType
    oil_viscosity: OilViscosity
    mileage_at_service: int
    next_service_mileage_due: int
    next_service_date_due: date
    notes: Optional[str] = None

    @validator("next_service_mileage_due")
    def validate_next_mileage(cls, v, values):
        if v < 2999:
            raise ValueError("Next service mileage due must be at least 2999 miles or greater")
        if "mileage_at_service" in values and v <= values["mileage_at_service"]:
            raise ValueError("Next service mileage must be greater than mileage at service")
        return v

    @validator("next_service_date_due")
    def validate_next_date(cls, v):
        from datetime import date as dt_date
        if v <= dt_date.today():
            raise ValueError("Next service date due must be a future date")
        return v
