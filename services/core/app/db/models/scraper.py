from uuid import UUID

from sqlalchemy import Enum as SAEnum, Float, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from .enums import JobModalityEnum, ScraperCategoryEnum, db_values


class JobOffer(Base):
    __tablename__ = "job_offers"

    offer_id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    category: Mapped[ScraperCategoryEnum] = mapped_column(
        SAEnum(
            ScraperCategoryEnum,
            name="scraper_category_enum",
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[str] = mapped_column(String(100), nullable=False)
    offer_location: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'No especificada'")
    )
    modality: Mapped[JobModalityEnum] = mapped_column(
        SAEnum(
            JobModalityEnum,
            name="job_modality_enum",
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
        server_default="NO ESPECIFICADO",
    )
    salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    offer_url: Mapped[str] = mapped_column(Text, nullable=False)
