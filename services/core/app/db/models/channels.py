from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    String,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from .enums import ChannelKindEnum, ScraperCategoryEnum, db_values


class Channel(Base):
    __tablename__ = "channels"
    __table_args__ = (
        CheckConstraint(
            "(kind = 'SCRAPER' AND scraper_category IS NOT NULL) OR "
            "(kind IS DISTINCT FROM 'SCRAPER' AND scraper_category IS NULL)",
            name="chk_channel_scraper_category",
        ),
    )

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    channel_name: Mapped[str] = mapped_column(String(100), nullable=False)
    guild_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("guilds.guild_id", ondelete="CASCADE", name="fk_channels_guild_id"),
        nullable=False,
    )
    kind: Mapped[ChannelKindEnum | None] = mapped_column(
        SAEnum(
            ChannelKindEnum,
            name="channel_kind_enum",
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=True,
    )
    scraper_category: Mapped[ScraperCategoryEnum | None] = mapped_column(
        SAEnum(
            ScraperCategoryEnum,
            name="scraper_category_enum",
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=True,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
