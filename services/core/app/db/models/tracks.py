from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, String, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class Track(Base):
    __tablename__ = "tracks"

    track_id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    track_name: Mapped[str] = mapped_column(String(255), nullable=False)
    artist: Mapped[str] = mapped_column(
        String(100), nullable=False, server_default=text("'Desconocido'")
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    track_url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
