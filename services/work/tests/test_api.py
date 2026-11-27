import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient

from services.work.api import (
    Settings,
    create_app,
    get_repository,
    get_request_repository,
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
    JobSearchRequest,
    RefreshOut,
    RefreshRequest,
    ScraperCategoryEnum,
    SearchRequestStatusEnum,
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
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0
        self.flushes = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, statement):
        return FakeResult()

    async def flush(self):
        self.flushes += 1

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


class FakeDatabase:
    def __init__(self, session):
        self.session_instance = session

    def session(self):
        return self.session_instance


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


class FakeRequestRepository:
    def __init__(self, records=None):
        self.records = records or []
        self.created = []
        self.success = []
        self.failed = []
        self.session = FakeSession()

    async def create(self, request):
        record = SimpleNamespace(
            request_id=uuid4(),
            request=request,
            parameters={
                "query": request.query,
                "num_pages": request.num_pages,
                "date_posted": request.date_posted,
                "country": request.country,
                "language": request.language,
                "location": request.location,
                "fields": ",".join(request.fields),
            },
        )
        self.created.append(record)
        return record

    async def mark_success(self, request_id, **kwargs):
        self.success.append((request_id, kwargs))

    async def mark_failed(self, request_id, *, error):
        self.failed.append((request_id, error))

    async def get(self, request_id):
        for record in self.records:
            if record.request_id == request_id:
                return record
        return None

    async def list_requests(self, **kwargs):
        return self.records, len(self.records)


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
        self.last_result = None

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
    paths = []

    async def handler(request):
        paths.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "data": {
                    "jobs": [
                        {
                            "job_title": "Backend Trainee",
                            "employer_name": "Xolo",
                            "job_city": "CDMX",
                            "job_country": "MX",
                            "job_is_remote": True,
                            "job_min_salary": 1000,
                            "job_max_salary": 2000,
                            "job_apply_link": "https://example.com/apply",
                            "job_posted_at_datetime_utc": "2026-11-26T00:00:00Z",
                        },
                        {"job_title": "incompleto"},
                    ]
                }
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

    assert paths == ["/search-v2"]
    assert len(offers) == 1
    assert offers[0].title == "Backend Trainee"
    assert offers[0].company == "Xolo"
    assert offers[0].offer_location == "CDMX, MX"
    assert offers[0].salary == 1500.0
    assert offers[0].modality == JobModalityEnum.REMOTO


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
    requests = FakeRequestRepository()
    service = JobSyncService(provider, FakeRepository(), requests)
    request = RefreshRequest(query="python intern")

    result = asyncio.run(service.refresh(request))

    assert isinstance(result, RefreshOut)
    assert result.total == 1
    assert result.inserted == 1
    assert result.request_id is not None
    assert provider.calls[0]["query"] == "python intern"
    assert len(requests.created) == 1
    assert len(requests.success) == 1


def make_session_request(session):
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(database=FakeDatabase(session)))
    )


def test_get_session_commits_on_success():
    session = FakeSession()
    generator = get_session(make_session_request(session))

    async def run():
        obtained = await anext(generator)
        assert obtained is session
        try:
            await anext(generator)
        except StopAsyncIteration:
            pass

    asyncio.run(run())
    assert session.commits == 1
    assert session.rollbacks == 0


def test_get_session_rollbacks_on_error():
    session = FakeSession()
    generator = get_session(make_session_request(session))

    async def run():
        await anext(generator)
        try:
            await generator.athrow(RuntimeError("boom"))
        except RuntimeError:
            pass

    asyncio.run(run())
    assert session.commits == 0
    assert session.rollbacks == 1


def make_search_request_record():
    return JobSearchRequest(
        request_id=uuid4(),
        query="developers or programers in Guadalajara Jalisco, Mexico",
        category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
        page=1,
        num_pages=1,
        date_posted="all",
        country="mex",
        language="spanish, english",
        location="Guadalajara, Jalisco, Mexico",
        fields=["employer_name", "job_publisher", "job_title", "job_country"],
        guidelines=[],
        parameters={"country": "mex"},
        jsearch_request_id="ae3ddca8-c132-46c1-bdd1-55c3d9efc32d",
        jsearch_status="OK",
        cursor=None,
        status=SearchRequestStatusEnum.OK,
        total_found=1,
        inserted=1,
        updated=0,
        error_message=None,
        created_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )


def test_refresh_uses_default_search_guidelines():
    offer = JobOfferUpsert(
        category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
        title="Backend Trainee",
        company="Xolo",
        offer_url="https://example.com/default",
    )
    provider = FakeProvider([offer])
    requests = FakeRequestRepository()
    service = JobSyncService(provider, FakeRepository(), requests)

    result = asyncio.run(service.refresh(RefreshRequest()))

    call = provider.calls[0]
    assert call["query"] == "developers or programers in Guadalajara Jalisco, Mexico"
    assert call["date_posted"] == "all"
    assert call["country"] == "mex"
    assert call["language"] == "spanish, english"
    assert call["location"] == "Guadalajara, Jalisco, Mexico"
    assert call["fields"] == [
        "employer_name",
        "job_publisher",
        "job_title",
        "job_country",
    ]
    assert call["guidelines"] == []
    assert requests.created[0].request.query == call["query"]
    assert requests.created[0].parameters["country"] == "mex"
    assert result.request_id is not None


def test_search_sends_guidelines_fields_and_captures_metadata():
    captured = []

    async def handler(request):
        captured.append(dict(request.url.params))
        return httpx.Response(
            200,
            json={
                "status": "OK",
                "request_id": "ae3ddca8-c132-46c1-bdd1-55c3d9efc32d",
                "parameters": {"query": "python junior"},
                "data": {
                    "jobs": [
                        {
                            "job_title": "Backend Trainee",
                            "employer_name": "Xolo",
                            "job_apply_link": "https://example.com/apply",
                        }
                    ],
                    "cursor": "next-cursor",
                },
            },
        )

    provider = make_provider(handler)
    offers = asyncio.run(
        provider.search(
            query="python",
            category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
            page=1,
            num_pages=1,
            date_posted="all",
            country="mex",
            language="spanish, english",
            location="Guadalajara, Jalisco, Mexico",
            fields=[
                "employer_name",
                "job_publisher",
                "job_title",
                "job_country",
            ],
            guidelines=["junior"],
        )
    )

    assert captured[0]["query"] == "python junior"
    assert captured[0]["date_posted"] == "all"
    assert captured[0]["country"] == "mex"
    assert captured[0]["language"] == "spanish, english"
    assert captured[0]["location"] == "Guadalajara, Jalisco, Mexico"
    assert captured[0]["fields"] == (
        "employer_name,job_publisher,job_title,job_country,job_apply_link"
    )
    assert len(offers) == 1
    assert provider.last_result is not None
    assert provider.last_result.status == "OK"
    assert provider.last_result.request_id == (
        "ae3ddca8-c132-46c1-bdd1-55c3d9efc32d"
    )
    assert provider.last_result.cursor == "next-cursor"
    assert provider.last_result.parameters == {"query": "python junior"}


def test_refresh_marks_request_failed_and_commits():
    class RaisingProvider:
        async def search(self, **kwargs):
            raise JSearchRateLimitError("rate limited")

    requests = FakeRequestRepository()
    service = JobSyncService(RaisingProvider(), FakeRepository(), requests)
    try:
        asyncio.run(service.refresh(RefreshRequest()))
    except JSearchRateLimitError:
        pass
    else:
        raise AssertionError("Expected JSearchRateLimitError")

    assert len(requests.failed) == 1
    assert requests.failed[0][1] == "rate limited"
    assert requests.success == []
    assert requests.session.commits == 1


def test_list_search_requests_endpoint():
    record = make_search_request_record()
    app = create_app(make_settings())
    app.dependency_overrides[get_request_repository] = lambda: FakeRequestRepository(
        [record]
    )
    with TestClient(app) as client:
        response = client.get("/jobs/requests")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["country"] == "mex"
    assert body["items"][0]["jsearch_status"] == "OK"


def test_get_search_request_endpoint():
    record = make_search_request_record()
    app = create_app(make_settings())
    app.dependency_overrides[get_request_repository] = lambda: FakeRequestRepository(
        [record]
    )
    with TestClient(app) as client:
        response = client.get(f"/jobs/requests/{record.request_id}")
    assert response.status_code == 200
    assert response.json()["query"] == record.query


def test_get_search_request_not_found():
    app = create_app(make_settings())
    app.dependency_overrides[get_request_repository] = lambda: FakeRequestRepository()
    with TestClient(app) as client:
        response = client.get(f"/jobs/requests/{uuid4()}")
    assert response.status_code == 404
