import asyncio
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

from .api import Settings
from .jsearch import (
    JSearchAuthError,
    JSearchError,
    JSearchProvider,
    JSearchRateLimitError,
    JSearchUnavailableError,
)
from .models import ScraperCategoryEnum


async def check() -> int:
    settings = Settings.from_env()
    if not settings.jsearch_api_key:
        raise SystemExit(
            "Falta JSEARCH_API_KEY en .env (raiz del repo). Pega la clave rotada ahi."
        )

    provider = JSearchProvider(
        api_key=settings.jsearch_api_key,
        api_host=settings.jsearch_api_host,
        timeout=settings.jsearch_timeout,
    )
    try:
        offers = await provider.search(
            query="python trainee",
            category=ScraperCategoryEnum.DESARROLLO_SOFTWARE,
            page=1,
            num_pages=1,
        )
    except JSearchAuthError as exc:
        raise SystemExit(
            "JSearch rechazo la credencial: revisa JSEARCH_API_KEY en .env."
        ) from exc
    except JSearchRateLimitError as exc:
        raise SystemExit(
            "JSearch devolvio 429 Too Many Requests: espera o revisa tu plan de RapidAPI."
        ) from exc
    except JSearchUnavailableError as exc:
        raise SystemExit("JSearch no esta disponible temporalmente (5xx).") from exc
    except JSearchError as exc:
        raise SystemExit(f"JSearch fallo: {exc}") from exc
    except httpx.HTTPError as exc:
        raise SystemExit(f"No se pudo conectar con JSearch: {exc}") from exc
    finally:
        await provider.close()

    if not offers:
        print("JSearch respondio, pero la consulta de prueba devolvio 0 ofertas.")
        return 0

    first = offers[0]
    print(
        f"JSearch OK: {len(offers)} ofertas. "
        f"Primera: {first.title} - {first.company}"
    )
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(check()))


if __name__ == "__main__":
    main()
