from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from src.api.v1.deps import get_current_user
from src.models.user import User

router = APIRouter()

@router.post("/")
async def geocode(
    payload: dict,
    current_user: User = Depends(get_current_user),
):
    return {"message": "geocode endpoint working"}


class GeocodeRequest(BaseModel):
    address: str = Field(..., min_length=3)
    language: str | None = Field(default="en")
    region: str | None = Field(default=None) 

class GeoPoint(BaseModel):
    lat: float
    lng: float

class PlaceEnrichment(BaseModel):
    display_name: str | None = None
    formatted_address: str | None = None

class LISLocationResponse(BaseModel):
    input_address: str
    normalized_address: str
    point: GeoPoint
    place_id: str | None = None
    enrichment: PlaceEnrichment | None = None
    status: str = "VALIDATED"
    provider: str = "google"
