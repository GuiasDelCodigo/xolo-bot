from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Enum as SAEnum, Float, String, Text, Uuid, text
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
    query: str = Field(min_length=2, max_length=200)
    category: ScraperCategoryEnum = ScraperCategoryEnum.DESARROLLO_SOFTWARE
    page: int = Field(default=1, ge=1)
    num_pages: int = Field(default=1, ge=1, le=5)


class RefreshOut(BaseModel):
    total: int
    inserted: int
    updated: int


class ErrorOut(BaseModel):
    detail: str
