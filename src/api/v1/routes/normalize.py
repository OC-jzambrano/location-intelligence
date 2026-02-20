from fastapi import APIRouter
from src.schemas.normalize import NormalizeRequest, NormalizeResponse
from src.services.lis import LISService

router = APIRouter(tags=["LIS"])

@router.post("", response_model=NormalizeResponse)
async def normalize(payload: NormalizeRequest) -> NormalizeResponse:
    svc = LISService()
    normalized = svc.normalize(payload.address)
    return NormalizeResponse(
        input_address=payload.address,
        normalized_address=normalized,
    )
