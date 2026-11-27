import asyncio
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from services.work.api import (
    Settings,
    create_app,
    get_repository,
    get_session,
    get_sync_service,
)
from services.work.jsearch import (
    JSearchAuthError,
    JSearchProvider,
    JSearchRateLimitError,
    JSearchUnavailableError,
    JobSyncService,
)
from services.work.models import (
    JobModalityEnum,
    JobOfferUpsert,
    RefreshOut,
    RefreshRequest,
    ScraperCategoryEnum,
)


def make_settings() -> Settings:
    return Settings(
        database_url="postgresql+psycopg://xolo:xolo@127.0.0.1:5432/xolo",
        api_host="127.0.0.1",
        api_port=8000,
        jsearch_api_key=None,
        jsearch_api_host="jsearch.p.rapidapi.com",
        jsearch_timeout=5.0,
        rapidapi_key=None,
        refresh_token="test-token",
        enable_refresh=True,
        log_level="WARNING",
    )


class FakeResult:
    def scalars(self):
        return self

    def first(self):
        return None


class FakeSession:
    async def execute(self, statement):
        return FakeResult()

    async def commit(self):
        return None


async def fake_session():
    return FakeSession()


class FakeRepository:
    def __init__(self, offers=None):
        self.offers = offers or []

    async def list_offers(self, **kwargs):
        return self.offers, len(self.offers)

    async def get_by_offer_id(self, offer_id):
        for offer in self.offers:
            if offer.offer_id == offer_id:
                return offer
        return None

    async def upsert_many(self, offers):
        return len(offers), 0


class FakeSyncService:
    async def refresh(self, request):
        return RefreshOut(total=1, inserted=1, updated=0)


class FailingSyncService:
    def __init__(self, error):
        self.error = error

    async def refresh(self, request):
        raise self.error


class FakeProvider:
    def __init__(self, offers):
        self.offers = offers
        self.calls = []

    async def search(self, **kwargs):
        self.calls.append(kwargs)
        return self.offers


def make_offer():
    return type(
        "Offer",
        (),
        {
            "offer_id": uuid4(),
            "category": ScraperCategoryEnum.DESARROLLO_SOFTWARE,
            "source": "jsearch",
            "title": "Trainee Python",
            "company": "Xolo",
            "offer_location": "Remoto",
            "modality": JobModalityEnum.REMOTO,
            "salary": 1000.0,
            "offer_url": "https://example.com/job/1",
            "published_at": None,
            "synced_at": None,
        },
    )()


def make_provider(handler) -> JSearchProvider:
    provider = JSearchProvider("dummy-key", "jsearch.p.rapidapi.com", 5.0)
    provider._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://jsearch.p.rapidapi.com",
        headers={},
        timeout=5.0,
    )
    return provider


def test_health_ok():
    app = create_app(make_settings())
    app.dependency_overrides[get_session] = fake_session
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_list_jobs_filters_and_pagination():
    offer = make_offer()
    app = create_app(make_settings())
    app.dependency_overrides[get_repository] = lambda: FakeRepository([offer])
    with TestClient(app) as client:
        response = client.get("/jobs?q=python&limit=5&offset=0")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 5
    assert body["items"][0]["title"] == "Trainee Python"


def test_get_job_not_found():
    app = create_app(make_settings())
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.get(f"/jobs/{uuid4()}")
    assert response.status_code == 404


def test_refresh_requires_token():
    app = create_app(make_settings())
    app.dependency_overrides[get_sync_service] = lambda: FakeSyncService()
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.post("/jobs/refresh", json={"query": "python"})
    assert response.status_code == 401


def test_refresh_with_token():
    app = create_app(make_settings())
    app.dependency_overrides[get_sync_service] = lambda: FakeSyncService()
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.post(
            "/jobs/refresh",
            headers={"X-Refresh-Token": "test-token"},
            json={"query": "python intern"},
        )
    assert response.status_code == 200
    assert response.json()["inserted"] == 1


def test_refresh_maps_auth_error_to_502():
    app = create_app(make_settings())
    app.dependency_overrides[get_sync_service] = lambda: FailingSyncService(
        JSearchAuthError("bad key")
    )
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.post(
            "/jobs/refresh",
            headers={"X-Refresh-Token": "test-token"},
            json={"query": "python intern"},
        )
    assert response.status_code == 502
    assert response.json()["detail"] == "JSearch rechazó la credencial RapidAPI."


def test_refresh_maps_rate_limit_to_429():
    app = create_app(make_settings())
    app.dependency_overrides[get_sync_service] = lambda: FailingSyncService(
        JSearchRateLimitError("rate limited")
    )
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.post(
            "/jobs/refresh",
            headers={"X-Refresh-Token": "test-token"},
            json={"query": "python intern"},
        )
    assert response.status_code == 429
    assert response.json()["detail"] == "JSearch devolvió 429 Too Many Requests."


def test_refresh_maps_unavailable_to_502():
    app = create_app(make_settings())
    app.dependency_overrides[get_sync_service] = lambda: FailingSyncService(
        JSearchUnavailableError("down")
    )
    app.dependency_overrides[get_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.post(
            "/jobs/refresh",
            headers={"X-Refresh-Token": "test-token"},
            json={"query": "python intern"},
        )
    assert response.status_code == 502
    assert response.json()["detail"] == "JSearch no está disponible temporalmente."


def test_search_maps_jsearch_payload():
    async def handler(request):
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "job_title": "Backend Trainee",
                        "employer_name": "Xolo",
                        "job_city": "CDMX",
                        "job_country": "MX",
                        "job_work_from_home": True,
                        "job_min_salary": 1000,
                        "job_max_salary": 2000,
                        "job_apply_link": "https://example.com/apply",
                        "job_posted_at_datetime_utc": "2026-11-26T00:00:00Z",
                    },
                    {"job_title": "incompleto"},
                ]
            },
        )

    provider = make_provider(handler)
    offers = asyncio.run(
        provider.search(
            query="python trainee",
            category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
            page=1,
            num_pages=1,
        )
    )

    assert len(offers) == 1
    assert offers[0].title == "Backend Trainee"
    assert offers[0].company == "Xolo"
    assert offers[0].offer_location == "CDMX, MX"
    assert offers[0].salary == 1500.0


def test_search_raises_on_rate_limit():
    async def handler(request):
        return httpx.Response(429, json={"message": "rate limited"})

    provider = make_provider(handler)
    try:
        asyncio.run(
            provider.search(
                query="python",
                category=ScraperCategoryEnum.DATOS_IA,
                page=1,
                num_pages=1,
            )
        )
    except JSearchRateLimitError:
        assert True
    else:
        raise AssertionError("Expected JSearchRateLimitError")


def test_refresh_calls_provider_and_upserts():
    offer = JobOfferUpsert(
        category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
        title="Intern Python",
        company="Xolo",
        offer_url="https://example.com/intern",
    )
    provider = FakeProvider([offer])
    service = JobSyncService(provider, FakeRepository())
    request = RefreshRequest(query="python intern")

    result = asyncio.run(service.refresh(request))

    assert isinstance(result, RefreshOut)
    assert result.total == 1
    assert result.inserted == 1
    assert provider.calls[0]["query"] == "python intern"
