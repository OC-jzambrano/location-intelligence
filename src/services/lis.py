from src.adapters.google_geocoding import GoogleGeocodingAdapter
from src.adapters.google_places_new import GooglePlacesNewAdapter
from src.schemas.geocode import LISLocationResponse, GeoPoint, PlaceEnrichment
from src.core.config import settings


class LISService:
    class NoResultsError(Exception): ...

    class ProviderTimeoutError(Exception): ...

    class ProviderError(Exception):
        def __init__(self, code: str):
            self.code = code

    def __init__(self):
        self.geocoder = GoogleGeocodingAdapter(api_key=settings.google_maps_api_key)
        self.places = GooglePlacesNewAdapter(api_key=settings.google_maps_api_key)

    def normalize(self, address: str) -> str:
        return " ".join(address.strip().split())

    async def resolve_location(
        self, address: str, language: str | None, region: str | None
    ) -> LISLocationResponse:
        normalized = self.normalize(address)

        # Phase 1: Geocoding (lat/lng + place_id) :contentReference[oaicite:10]{index=10}
        try:
            geocode_res = await self.geocoder.geocode(normalized, language=language, region=region)
        except ValueError as e:
            if str(e) == "NO_RESULTS":
                raise self.NoResultsError()
            raise self.ProviderError(code="GEOCODING_FAILED")
        except Exception:
            raise self.ProviderError(code="GEOCODING_FAILED")

        enrichment = None

        # Phase 2: Places New (enrich via place_id) :contentReference[oaicite:11]{index=11}
        if geocode_res.place_id:
            try:
                place = await self.places.get_place_details(geocode_res.place_id)
                enrichment = PlaceEnrichment(
                    display_name=place.display_name,
                    formatted_address=place.formatted_address,
                )
            except Exception:
                enrichment = None

        return LISLocationResponse(
            input_address=address,
            normalized_address=normalized,
            point=GeoPoint(lat=geocode_res.lat, lng=geocode_res.lng),
            place_id=geocode_res.place_id,
            enrichment=enrichment,
            status="VALIDATED",
            provider="google",
        )
