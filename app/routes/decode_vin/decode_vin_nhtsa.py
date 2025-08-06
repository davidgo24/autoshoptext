# app/routes/vin.py
import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter()

@router.get("/decode_vin/{vin}")
async def decode_vin(vin: str):
    if len(vin) != 17:
        raise HTTPException(status_code=400, detail="VIN must be 17 characters long.")
    
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVin/{vin}?format=json"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()

    if not data or "Results" not in data:
        raise HTTPException(status_code=500, detail="Failed to decode VIN.")

    result = {
        "vin": vin,
        "make": None,
        "model": None,
        "year": None,
        "trim": None
    }

    for item in data["Results"]:
        label = item.get("Variable")
        value = item.get("Value")
        if not value:
            continue

        if label == "Make":
            result["make"] = value.upper()
        elif label == "Model":
            result["model"] = value.upper()
        elif label == "Model Year":
            result["year"] = int(value)
        elif label == "Trim":
            result["trim"] = value.upper()

    return result
