from pydantic import BaseModel, constr
from typing import Optional
from typing_extensions import Annotated

class VinCreate(BaseModel):
    vin: Annotated[str, constr(min_length=17, max_length=17)]
    make: str
    model: str
    year: int
    trim: Optional[str] = None
    plate: Optional[str] = None