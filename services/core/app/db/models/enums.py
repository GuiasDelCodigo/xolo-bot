from enum import Enum


def db_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


class RolEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"


class ChannelKindEnum(str, Enum):
    WELCOME = "WELCOME"
    MUSIC = "MUSIC"
    SCRAPER = "SCRAPER"
    GITHUB = "GITHUB"


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
