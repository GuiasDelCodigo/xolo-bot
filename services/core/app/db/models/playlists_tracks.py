from uuid import UUID

from sqlalchemy import ForeignKey, Integer, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class PlaylistTrack(Base):
    __tablename__ = "playlists_tracks"
    __table_args__ = (
        UniqueConstraint("playlist_id", "position", name="uq_playlists_track_position"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    playlist_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "playlists.playlist_id",
            ondelete="CASCADE",
            name="fk_playlists_tracks_playlist_id",
        ),
        nullable=False,
    )
    track_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("tracks.track_id", ondelete="CASCADE", name="fk_playlists_tracks_track_id"),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
