from datetime import datetime, timezone

import httpx

from .models import (
    JobModalityEnum,
    JobOfferUpsert,
    RefreshOut,
    RefreshRequest,
    ScraperCategoryEnum,
)
from .storage import JobOfferRepository


class JSearchError(Exception):
    pass


class JSearchAuthError(JSearchError):
    pass


class JSearchRateLimitError(JSearchError):
    pass


class JSearchUnavailableError(JSearchError):
    pass


class JSearchProvider:
    def __init__(self, api_key: str | None, api_host: str, timeout: float) -> None:
        self._client = httpx.AsyncClient(
            base_url="https://jsearch.p.rapidapi.com",
            headers={
                "x-rapidapi-key": api_key or "",
                "x-rapidapi-host": api_host,
            },
            timeout=timeout,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search(
        self,
        *,
        query: str,
        category: ScraperCategoryEnum,
        page: int,
        num_pages: int,
    ) -> list[JobOfferUpsert]:
        response = await self._client.get(
            "/search",
            params={"query": query, "page": page, "num_pages": num_pages},
        )

        if response.status_code in (401, 403):
            raise JSearchAuthError("JSearch rechazó la credencial RapidAPI.")
        if response.status_code == 429:
            raise JSearchRateLimitError("JSearch devolvió 429 Too Many Requests.")
        if response.status_code >= 500:
            raise JSearchUnavailableError("JSearch no está disponible temporalmente.")
        if response.status_code >= 400:
            raise JSearchError(f"JSearch devolvió {response.status_code}.")

        payload = response.json()
        raw_offers = payload.get("data", [])
        if not isinstance(raw_offers, list):
            raise JSearchError("Respuesta inesperada de JSearch: data no es una lista.")

        mapped = []
        for raw in raw_offers:
            offer = self._map(raw, category)
            if offer is not None:
                mapped.append(offer)
        return mapped

    @staticmethod
    def _salary(raw: dict) -> float | None:
        values = []
        for key in ("job_min_salary", "job_max_salary"):
            value = raw.get(key)
            if value is not None:
                try:
                    values.append(float(value))
                except (TypeError, ValueError):
                    continue
        if not values:
            return None
        return sum(values) / len(values)

    @staticmethod
    def _published_at(raw: dict) -> datetime | None:
        value = raw.get("job_posted_at_datetime_utc")
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed

    @classmethod
    def _map(cls, raw: dict, category: ScraperCategoryEnum) -> JobOfferUpsert | None:
        if not isinstance(raw, dict):
            return None

        title = str(raw.get("job_title") or "").strip()
        company = str(raw.get("employer_name") or "").strip()
        offer_url = str(
            raw.get("job_apply_link") or raw.get("job_google_link") or ""
        ).strip()
        if not title or not company or not offer_url:
            return None

        location_parts = []
        for key in ("job_city", "job_country"):
            value = str(raw.get(key) or "").strip()
            if value:
                location_parts.append(value)
        offer_location = ", ".join(location_parts) or "No especificada"

        modality = (
            JobModalityEnum.REMOTO
            if raw.get("job_work_from_home")
            else JobModalityEnum.NOT_SPECIFIED
        )

        return JobOfferUpsert(
            category=category,
            source="jsearch",
            title=title[:200],
            company=company[:100],
            offer_location=offer_location[:100],
            modality=modality,
            salary=cls._salary(raw),
            offer_url=offer_url,
            published_at=cls._published_at(raw),
        )


class JobSyncService:
    def __init__(
        self, provider: JSearchProvider, repository: JobOfferRepository
    ) -> None:
        self.provider = provider
        self.repository = repository

    async def refresh(self, request: RefreshRequest) -> RefreshOut:
        offers = await self.provider.search(
            query=request.query,
            category=request.category,
            page=request.page,
            num_pages=request.num_pages,
        )
        inserted, updated = await self.repository.upsert_many(offers)
        return RefreshOut(total=len(offers), inserted=inserted, updated=updated)
