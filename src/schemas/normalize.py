from pydantic import BaseModel, Field
from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def normalize(payload: dict):
    return {"message": "normalize endpoint working"}


class NormalizeRequest(BaseModel):
    address: str = Field(..., min_length=3)

class NormalizeResponse(BaseModel):
    input_address: str
    normalized_address: str
