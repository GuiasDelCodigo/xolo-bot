from datetime import datetime
from enum import Enum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy import DateTime, Enum as SAEnum, Float, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import UniqueConstraint


def db_values(enum: type[Enum]) -> list[str]:
    return [member.value for member in enum]


class ScraperCategoryEnum(str, Enum):
    DESARROLLO_SOFTWARE = "DESARROLLO_SOFTWARE"
    DATOS_IA = "DATOS_IA"
    CIBERSEGURIDAD = "CIBERSEGURIDAD"
    CLOUD_DEVOPS = "CLOUD_DEVOPS"


class JobModalityEnum(str, Enum):
    PRESENCIAL = "PRESENCIAL"
    REMOTO = "REMOTO"
    HIBRIDO = "HIBRIDO"
    NOT_SPECIFIED = "NO ESPECIFICADO"


class Base(DeclarativeBase):
    pass


class JobOffer(Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        UniqueConstraint("url_hash", name="uq_job_offers_url_hash"),
    )

    offer_id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    category: Mapped[ScraperCategoryEnum] = mapped_column(
        SAEnum(
            ScraperCategoryEnum,
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    offer_location: Mapped[str] = mapped_column(
        String(100), nullable=False, default="No especificada"
    )
    modality: Mapped[JobModalityEnum] = mapped_column(
        SAEnum(JobModalityEnum, native_enum=True, values_callable=db_values),
        nullable=False,
        default=JobModalityEnum.NOT_SPECIFIED,
    )
    salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    offer_url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(32), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )


class SearchRequestStatusEnum(str, Enum):
    PENDING = "PENDING"
    OK = "OK"
    FAILED = "FAILED"


class JobSearchRequest(Base):
    __tablename__ = "job_search_requests"

    request_id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    query: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[ScraperCategoryEnum] = mapped_column(
        SAEnum(
            ScraperCategoryEnum,
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
    )
    page: Mapped[int] = mapped_column(nullable=False, default=1)
    num_pages: Mapped[int] = mapped_column(nullable=False, default=1)
    date_posted: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    language: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    fields: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    guidelines: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    jsearch_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    jsearch_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cursor: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[SearchRequestStatusEnum] = mapped_column(
        SAEnum(
            SearchRequestStatusEnum,
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
        default=SearchRequestStatusEnum.PENDING,
    )
    total_found: Mapped[int] = mapped_column(nullable=False, default=0)
    inserted: Mapped[int] = mapped_column(nullable=False, default=0)
    updated: Mapped[int] = mapped_column(nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class JobOfferUpsert(BaseModel):
    category: ScraperCategoryEnum
    source: str = "jsearch"
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(min_length=1, max_length=100)
    offer_location: str = "No especificada"
    modality: JobModalityEnum = JobModalityEnum.NOT_SPECIFIED
    salary: float | None = None
    offer_url: str = Field(min_length=1)
    published_at: datetime | None = None


class JobOfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    offer_id: UUID
    category: ScraperCategoryEnum
    source: str
    title: str
    company: str
    offer_location: str
    modality: JobModalityEnum
    salary: float | None
    offer_url: str
    published_at: datetime | None
    synced_at: datetime | None


class JobPage(BaseModel):
    items: list[JobOfferOut]
    total: int
    limit: int
    offset: int


class HealthOut(BaseModel):
    status: str
    database: str


class RefreshRequest(BaseModel):
    query: str = Field(
        default="developers or programers in Guadalajara Jalisco, Mexico",
        min_length=2,
        max_length=200,
    )
    category: ScraperCategoryEnum = ScraperCategoryEnum.DESARROLLO_SOFTWARE
    page: int = Field(default=1, ge=1)
    num_pages: int = Field(default=1, ge=1, le=5)
    date_posted: Literal["all", "today", "3days", "week", "month"] = "all"
    country: str = Field(default="mex", max_length=10)
    language: str = Field(default="spanish, english", max_length=100)
    location: str = Field(default="Guadalajara, Jalisco, Mexico", max_length=200)
    fields: list[str] = Field(
        default_factory=lambda: [
            "employer_name",
            "job_publisher",
            "job_title",
            "job_country",
        ],
        max_length=20,
    )
    guidelines: list[
        Annotated[str, StringConstraints(min_length=1, max_length=200)]
    ] = Field(default_factory=list, max_length=10)


class RefreshOut(BaseModel):
    total: int
    inserted: int
    updated: int
    request_id: UUID | None = None


class ErrorOut(BaseModel):
    detail: str


class JobSearchRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    request_id: UUID
    query: str
    category: ScraperCategoryEnum
    page: int
    num_pages: int
    date_posted: str | None
    country: str | None
    language: str | None
    location: str | None
    fields: list[str] | None
    guidelines: list[str]
    parameters: dict
    jsearch_request_id: str | None
    jsearch_status: str | None
    cursor: str | None
    status: SearchRequestStatusEnum
    total_found: int
    inserted: int
    updated: int
    error_message: str | None
    created_at: datetime
    finished_at: datetime | None


class JobSearchRequestPage(BaseModel):
    items: list[JobSearchRequestOut]
    total: int
    limit: int
    offset: int
