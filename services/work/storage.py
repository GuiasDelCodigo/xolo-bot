from datetime import datetime, timezone
from hashlib import md5
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import JobModalityEnum, JobOffer, JobOfferUpsert, ScraperCategoryEnum


def url_hash(offer_url: str) -> str:
    return md5(offer_url.encode("utf-8")).hexdigest()


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(url, pool_pre_ping=True)
        self.sessionmaker = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    def session(self) -> AsyncSession:
        return self.sessionmaker()

    async def close(self) -> None:
        await self.engine.dispose()


class JobOfferRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_offers(
        self,
        *,
        q: str | None,
        category: ScraperCategoryEnum | None,
        modality: JobModalityEnum | None,
        company: str | None,
        source: str | None,
        location: str | None,
        min_salary: float | None,
        max_salary: float | None,
        limit: int,
        offset: int,
    ) -> tuple[list[JobOffer], int]:
        conditions = []
        if q:
            pattern = f"%{q}%"
            conditions.append(
                or_(
                    JobOffer.title.ilike(pattern),
                    JobOffer.company.ilike(pattern),
                )
            )
        if category:
            conditions.append(JobOffer.category == category)
        if modality:
            conditions.append(JobOffer.modality == modality)
        if company:
            conditions.append(JobOffer.company.ilike(f"%{company}%"))
        if source:
            conditions.append(JobOffer.source == source)
        if location:
            conditions.append(JobOffer.offer_location.ilike(f"%{location}%"))
        if min_salary is not None:
            conditions.append(JobOffer.salary >= min_salary)
        if max_salary is not None:
            conditions.append(JobOffer.salary <= max_salary)

        items_stmt = (
            select(JobOffer)
            .where(*conditions)
            .order_by(JobOffer.synced_at.desc(), JobOffer.offer_id)
            .limit(limit)
            .offset(offset)
        )
        total_stmt = select(func.count()).select_from(JobOffer).where(*conditions)

        items = list((await self.session.execute(items_stmt)).scalars().all())
        total = int((await self.session.execute(total_stmt)).scalar_one())
        return items, total

    async def get_by_offer_id(self, offer_id: UUID) -> JobOffer | None:
        stmt = select(JobOffer).where(JobOffer.offer_id == offer_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_url_hash(self, digest: str) -> JobOffer | None:
        stmt = select(JobOffer).where(JobOffer.url_hash == digest)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_many(self, offers: list[JobOfferUpsert]) -> tuple[int, int]:
        inserted = 0
        updated = 0
        now = datetime.now(timezone.utc)

        for offer in offers:
            digest = url_hash(offer.offer_url)
            existing = await self.get_by_url_hash(digest)
            if existing:
                existing.title = offer.title
                existing.company = offer.company
                existing.category = offer.category
                existing.source = offer.source
                existing.offer_location = offer.offer_location
                existing.modality = offer.modality
                existing.salary = offer.salary
                existing.offer_url = offer.offer_url
                existing.published_at = offer.published_at
                existing.synced_at = now
                updated += 1
            else:
                self.session.add(
                    JobOffer(
                        category=offer.category,
                        source=offer.source,
                        title=offer.title,
                        company=offer.company,
                        offer_location=offer.offer_location,
                        modality=offer.modality,
                        salary=offer.salary,
                        offer_url=offer.offer_url,
                        url_hash=digest,
                        published_at=offer.published_at,
                        synced_at=now,
                    )
                )
                inserted += 1

        await self.session.flush()
        return inserted, updated
