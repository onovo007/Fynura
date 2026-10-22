"""IOM DTM v3 adapter. Live use remains disabled until a subscription key is supplied."""

from datetime import date
from urllib.parse import urlparse

import httpx

from backend.models.contextual import ContextObservation

ALLOWED_HOST_SUFFIX = ".iom.int"
PILOT_ISO3 = {"COD", "KEN", "NGA", "UGA"}


class IOMDTMAdapter:
    source_id = "iom_dtm_v3"
    licence_id = "iom-dtm-public-terms-2026-10"

    @staticmethod
    def _validate_base_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or not (
            parsed.hostname == "iom.int" or parsed.hostname.endswith(ALLOWED_HOST_SUFFIX)
        ):
            raise ValueError("DTM API base URL must use an approved IOM HTTPS host")

    async def retrieve(self, endpoint: str, subscription_key: str, *, client=None) -> dict:
        self._validate_base_url(endpoint)
        if not subscription_key or len(subscription_key) < 12:
            raise ValueError("A DTM v3 subscription key is required")
        headers = {"Ocp-Apim-Subscription-Key": subscription_key, "User-Agent": "Fynura contextual-data validation/1.0"}
        if client is None:
            async with httpx.AsyncClient(timeout=30, follow_redirects=False) as owned:
                response = await owned.get(endpoint, headers=headers)
        else:
            response = await client.get(endpoint, headers=headers)
        response.raise_for_status()
        if "json" not in response.headers.get("content-type", "").lower():
            raise ValueError("DTM endpoint did not return JSON")
        return response.json()

    def parse_records(self, records: list[dict], *, source_url: str, retrieved_at=None) -> list[ContextObservation]:
        self._validate_base_url(source_url)
        output = []
        for row in records:
            iso3 = str(row.get("iso3") or row.get("countryCode") or "").upper()
            if iso3 not in PILOT_ISO3:
                continue
            value = row.get("idpIndividuals", row.get("value"))
            end = row.get("assessmentDate", row.get("referenceEnd"))
            if value is None or not end:
                raise ValueError("DTM record lacks a displacement value or assessment date")
            level = str(row.get("adminLevel") or "country").lower()
            level = {"admin 1": "admin1", "admin 2": "admin2", "0": "country", "1": "admin1", "2": "admin2"}.get(level, level)
            if level not in {"country", "admin1", "admin2"}:
                raise ValueError("Unsupported DTM geography level")
            values = {
                "source_id": self.source_id, "context_type": "displacement_stock",
                "geography_name": str(row.get("locationName") or row.get("countryName") or iso3),
                "geography_code": str(row.get("locationCode") or iso3), "geography_level": level,
                "reference_end": date.fromisoformat(str(end)[:10]), "value": float(value), "unit": "persons",
                "source_url": source_url, "assessment_round": str(row.get("round") or "") or None,
                "method": "IOM DTM baseline or location assessment aggregate", "licence_id": self.licence_id,
                "attribution": f"International Organization for Migration (IOM), DTM, {str(end)[:7]}",
                "privacy_classification": "public_aggregate", "validation_status": "quarantined",
                "limitations": ["Assessment frequency and coverage vary by operation.", "Displacement is contextual and does not establish disease transmission."],
            }
            if retrieved_at is not None:
                values["retrieved_at"] = retrieved_at
            output.append(ContextObservation(**values))
        return output

