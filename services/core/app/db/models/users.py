from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SAEnum, String, text
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from .enums import RolEnum, db_values


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    user_name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    rol: Mapped[RolEnum] = mapped_column(
        SAEnum(
            RolEnum,
            name="rol_enum",
            native_enum=True,
            values_callable=db_values,
        ),
        nullable=False,
        server_default="USER",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
