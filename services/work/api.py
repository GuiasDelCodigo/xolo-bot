import hmac
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .jsearch import (
    JSearchAuthError,
    JSearchError,
    JSearchProvider,
    JSearchRateLimitError,
    JSearchUnavailableError,
    JobSyncService,
)
from .models import (
    HealthOut,
    JobModalityEnum,
    JobOfferOut,
    JobPage,
    RefreshOut,
    RefreshRequest,
    ScraperCategoryEnum,
)
from .storage import Database, JobOfferRepository

TRUE_VALUES = {"1", "true", "yes", "on", "y", "sí", "si"}


class Settings:
    def __init__(
        self,
        *,
        database_url: str,
        api_host: str,
        api_port: int,
        jsearch_api_key: str | None,
        jsearch_api_host: str,
        jsearch_timeout: float,
        rapidapi_key: str | None,
        refresh_token: str,
        enable_refresh: bool,
        log_level: str,
    ) -> None:
        self.database_url = database_url
        self.api_host = api_host
        self.api_port = api_port
        self.jsearch_api_key = jsearch_api_key
        self.jsearch_api_host = jsearch_api_host
        self.jsearch_timeout = jsearch_timeout
        self.rapidapi_key = rapidapi_key
        self.refresh_token = refresh_token
        self.enable_refresh = enable_refresh
        self.log_level = log_level

    @classmethod
    def from_env(cls) -> "Settings":
        import os

        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg://xolo:change_me@127.0.0.1:5432/xolo",
        )
        jsearch_api_key = os.getenv("JSEARCH_API_KEY") or None
        refresh_token = os.getenv("REFRESH_TOKEN") or ""
        enable_refresh = (
            os.getenv("ENABLE_REFRESH", "true").strip().lower() in TRUE_VALUES
        )
        if enable_refresh and not refresh_token:
            raise RuntimeError(
                "REFRESH_TOKEN es obligatorio cuando ENABLE_REFRESH=true."
            )

        return cls(
            database_url=database_url,
            api_host=os.getenv("API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("API_PORT", "8000")),
            jsearch_api_key=jsearch_api_key,
            jsearch_api_host=os.getenv(
                "JSEARCH_API_HOST", "jsearch.p.rapidapi.com"
            ),
            jsearch_timeout=float(os.getenv("JSEARCH_TIMEOUT", "5.0")),
            rapidapi_key=os.getenv("RAPIDAPI_KEY") or None,
            refresh_token=refresh_token,
            enable_refresh=enable_refresh,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.database.session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_provider(request: Request) -> JSearchProvider:
    return request.app.state.jsearch


def get_repository(
    session: AsyncSession = Depends(get_session),
) -> JobOfferRepository:
    return JobOfferRepository(session)


def get_sync_service(
    provider: JSearchProvider = Depends(get_provider),
    repository: JobOfferRepository = Depends(get_repository),
) -> JobSyncService:
    return JobSyncService(provider, repository)


async def verify_rapidapi_key(
    request: Request,
    x_rapidapi_key: str | None = Header(default=None),
) -> None:
    expected = request.app.state.settings.rapidapi_key
    if not expected:
        return
    if not x_rapidapi_key or not hmac.compare_digest(x_rapidapi_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-RapidAPI-Key inválida.",
        )


async def verify_refresh_token(
    request: Request,
    x_refresh_token: str | None = Header(default=None),
) -> None:
    expected = request.app.state.settings.refresh_token
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El refresco está deshabilitado.",
        )
    if not x_refresh_token or not hmac.compare_digest(x_refresh_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Refresh-Token inválido.",
        )


health_router = APIRouter(tags=["health"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
refresh_router = APIRouter(prefix="/jobs", tags=["refresh"])


@health_router.get("/health", response_model=HealthOut)
async def health(session: AsyncSession = Depends(get_session)) -> HealthOut:
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Base de datos no disponible.",
        ) from exc
    return HealthOut(status="ok", database="ok")


@jobs_router.get("", response_model=JobPage)
async def list_jobs(
    q: str | None = Query(default=None, max_length=100),
    category: ScraperCategoryEnum | None = Query(default=None),
    modality: JobModalityEnum | None = Query(default=None),
    company: str | None = Query(default=None, max_length=100),
    source: str | None = Query(default=None, max_length=100),
    location: str | None = Query(default=None, max_length=100),
    min_salary: float | None = Query(default=None, ge=0),
    max_salary: float | None = Query(default=None, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    repository: JobOfferRepository = Depends(get_repository),
) -> JobPage:
    if min_salary is not None and max_salary is not None and min_salary > max_salary:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="min_salary no puede ser mayor que max_salary.",
        )

    items, total = await repository.list_offers(
        q=q,
        category=category,
        modality=modality,
        company=company,
        source=source,
        location=location,
        min_salary=min_salary,
        max_salary=max_salary,
        limit=limit,
        offset=offset,
    )
    return JobPage(
        items=[JobOfferOut.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@jobs_router.get("/{offer_id}", response_model=JobOfferOut)
async def get_job(
    offer_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> JobOfferOut:
    repository = JobOfferRepository(session)
    offer = await repository.get_by_offer_id(offer_id)
    if offer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una vacante con ese offer_id.",
        )
    return JobOfferOut.model_validate(offer)


@refresh_router.post("/refresh", response_model=RefreshOut)
async def refresh_jobs(
    request: RefreshRequest,
    service: JobSyncService = Depends(get_sync_service),
    _token_ok: None = Depends(verify_refresh_token),
) -> RefreshOut:
    try:
        return await service.refresh(request)
    except JSearchAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="JSearch rechazó la credencial RapidAPI.",
        ) from exc
    except JSearchRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="JSearch devolvió 429 Too Many Requests.",
        ) from exc
    except JSearchUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="JSearch no está disponible temporalmente.",
        ) from exc
    except JSearchError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"JSearch falló: {exc}",
        ) from exc


def create_app(settings: Settings) -> FastAPI:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO)
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        database = Database(settings.database_url)
        jsearch = JSearchProvider(
            api_key=settings.jsearch_api_key,
            api_host=settings.jsearch_api_host,
            timeout=settings.jsearch_timeout,
        )
        app.state.settings = settings
        app.state.database = database
        app.state.jsearch = jsearch
        try:
            yield
        finally:
            await jsearch.close()
            await database.close()

    app = FastAPI(
        title="Xolo Jobs API",
        version="1.0.0",
        description="API de vacantes con PostgreSQL y JSearch.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.include_router(health_router)
    app.include_router(jobs_router, dependencies=[Depends(verify_rapidapi_key)])
    if settings.enable_refresh:
        app.include_router(
            refresh_router, dependencies=[Depends(verify_refresh_token)]
        )
    return app
