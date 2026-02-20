from fastapi import APIRouter, Depends, HTTPException, status
from src.api.v1.deps import get_current_user
from src.models.user import User
from src.schemas.geocode import GeocodeRequest, LISLocationResponse
from src.services.lis import LISService

router = APIRouter(tags=["LIS"])

@router.post("", response_model=LISLocationResponse)
async def geocode(
    payload: GeocodeRequest,
    current_user: User = Depends(get_current_user),
) -> LISLocationResponse:
    svc = LISService()
    try:
        return await svc.resolve_location(payload.address, payload.language, payload.region)
    except svc.NoResultsError:
        raise HTTPException(status_code=422, detail="NO_RESULTS")
    except svc.ProviderTimeoutError:
        raise HTTPException(status_code=422, detail="TIMEOUT")
    except svc.ProviderError as e:
        raise HTTPException(status_code=422, detail=f"PROVIDER_ERROR:{e.code}")
