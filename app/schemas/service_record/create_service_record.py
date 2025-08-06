from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import date

OIL_TYPES = {
    "synthetic",
    "synthetic-blend",
    "full synthetic",
    "high-mileage synthetic-blend",
    "high-mileage full-synthetic",
}

VALID_VISCOSITIES = {
    "0W-20", "5W-20", "5W-30", "10W-30", "15W-40",  # extend as needed
}

class ServiceRecordCreate(BaseModel):
    vin_id: int
    service_date: Optional[date] = None
    oil_type: str = Field(..., description="Oil type from allowed list")
    oil_viscosity: str = Field(..., description="Oil viscosity from allowed list")
    mileage_at_service: int
    next_service_mileage_due: int
    next_service_date_due: date
    notes: Optional[str] = None

    @validator("oil_type")
    def check_oil_type(cls, v):
        if v.lower() not in OIL_TYPES:
            raise ValueError(f"Oil type '{v}' is invalid. Must be one of {OIL_TYPES}")
        return v.lower()

    @validator("oil_viscosity")
    def check_oil_viscosity(cls, v):
        if v.upper() not in VALID_VISCOSITIES:
            raise ValueError(f"Oil viscosity '{v}' is invalid. Must be one of {VALID_VISCOSITIES}")
        return v.upper()

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
