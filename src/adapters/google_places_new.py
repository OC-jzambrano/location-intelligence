import httpx
from dataclasses import dataclass


@dataclass
class PlaceDetails:
    display_name: str | None
    formatted_address: str | None


class GooglePlacesNewAdapter:
    def __init__(self, api_key: str, base_url: str = "https://places.googleapis.com/v1"):
        self.api_key = api_key
        self.base_url = base_url

    async def get_place_details(self, place_id: str) -> PlaceDetails:
        # Places New: GET /places/{place_id}
        url = f"{self.base_url}/places/{place_id}"

        headers = {
            "X-Goog-Api-Key": self.api_key,
            # contentReference[oaicite:8]{index=8}
            "X-Goog-FieldMask": "id,displayName,formattedAddress",
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers=headers)

        if r.status_code >= 400:
            raise RuntimeError(f"PLACES_ERROR:{r.status_code}")

        data = r.json()

        display = None
        dn = data.get("displayName")
        if isinstance(dn, dict):
            display = dn.get("text")

        return PlaceDetails(
            display_name=display,
            formatted_address=data.get("formattedAddress"),
        )
