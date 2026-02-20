import httpx
from dataclasses import dataclass


@dataclass
class GeocodeResult:
    lat: float
    lng: float
    place_id: str | None


class GoogleGeocodingAdapter:
    def __init__(
        self, api_key: str, base_url: str = "https://maps.googleapis.com/maps/api/geocode/json"
    ):
        self.api_key = api_key
        self.base_url = base_url

    async def geocode(
        self, address: str, language: str | None = None, region: str | None = None
    ) -> GeocodeResult:
        params = {"address": address, "key": self.api_key}
        if language:
            params["language"] = language
        if region:
            params["region"] = region

        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(self.base_url, params=params)

        data = r.json()
        status_ = data.get("status")

        if status_ == "ZERO_RESULTS":
            raise ValueError("NO_RESULTS")
        if status_ != "OK":
            raise RuntimeError(f"GEOCODING_ERROR:{status_}")

        first = data["results"][0]
        loc = first["geometry"]["location"]
        return GeocodeResult(
            lat=loc["lat"],
            lng=loc["lng"],
            place_id=first.get("place_id"),
        )
