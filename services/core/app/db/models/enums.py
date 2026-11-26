from enum import Enum


def db_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class RolEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"

