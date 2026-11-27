from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .models import (
    JobModalityEnum,
    JobOfferUpsert,
    RefreshOut,
    RefreshRequest,
    ScraperCategoryEnum,
)
from .storage import JobOfferRepository, JobSearchRequestRepository


REQUIRED_FIELDS = ("job_title", "employer_name", "job_apply_link")


@dataclass
class JSearchResultMeta:
    request_id: str | None
    status: str | None
    parameters: dict
    cursor: str | None


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
        self.last_result: JSearchResultMeta | None = None

    async def close(self) -> None:
        await self._client.aclose()

    async def search(
        self,
        *,
        query: str,
        category: ScraperCategoryEnum,
        page: int,
        num_pages: int,
        date_posted: str = "all",
        country: str | None = None,
        language: str | None = None,
        location: str | None = None,
        fields: list[str] | None = None,
        guidelines: list[str] | None = None,
    ) -> list[JobOfferUpsert]:
        effective_query = " ".join([query, *(guidelines or [])]).strip()
        params: dict[str, str | int] = {
            "query": effective_query,
            "page": page,
            "num_pages": num_pages,
            "date_posted": date_posted,
        }
        if country:
            params["country"] = country
        if language:
            params["language"] = language
        if location:
            params["location"] = location
        if fields:
            merged_fields = list(dict.fromkeys([*fields, *REQUIRED_FIELDS]))
            params["fields"] = ",".join(merged_fields)

        response = await self._client.get("/search-v2", params=params)

        if response.status_code in (401, 403):
            raise JSearchAuthError("JSearch rechazó la credencial RapidAPI.")
        if response.status_code == 429:
            raise JSearchRateLimitError("JSearch devolvió 429 Too Many Requests.")
        if response.status_code >= 500:
            raise JSearchUnavailableError("JSearch no está disponible temporalmente.")
        if response.status_code >= 400:
            raise JSearchError(f"JSearch devolvió {response.status_code}.")

        payload = response.json()
        raw_data = payload.get("data", [])
        payload_data = raw_data if isinstance(raw_data, dict) else {}
        self.last_result = JSearchResultMeta(
            request_id=payload.get("request_id"),
            status=payload.get("status"),
            parameters=payload.get("parameters") or {},
            cursor=payload_data.get("cursor"),
        )
        if isinstance(raw_data, dict):
            raw_offers = raw_data.get("jobs", [])
        else:
            raw_offers = raw_data
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

        is_remote = raw.get("job_work_from_home")
        if is_remote is None:
            is_remote = raw.get("job_is_remote")
        modality = (
            JobModalityEnum.REMOTO
            if is_remote
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
        self,
        provider: JSearchProvider,
        repository: JobOfferRepository,
        requests: JobSearchRequestRepository,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.requests = requests

    async def refresh(self, request: RefreshRequest) -> RefreshOut:
        record = await self.requests.create(request)
        try:
            offers = await self.provider.search(
                query=request.query,
                category=request.category,
                page=request.page,
                num_pages=request.num_pages,
                date_posted=request.date_posted,
                country=request.country,
                language=request.language,
                location=request.location,
                fields=request.fields,
                guidelines=request.guidelines,
            )
        except JSearchError as exc:
            await self.requests.mark_failed(record.request_id, error=str(exc))
            await self.requests.session.commit()
            raise

        inserted, updated = await self.repository.upsert_many(offers)
        await self.requests.mark_success(
            record.request_id,
            total=len(offers),
            inserted=inserted,
            updated=updated,
            meta=self.provider.last_result,
        )
        return RefreshOut(
            total=len(offers),
            inserted=inserted,
            updated=updated,
            request_id=record.request_id,
        )
