import asyncio
import selectors
import sys

from dotenv import load_dotenv

load_dotenv()

import uvicorn

from .api import Settings, create_app

settings = Settings.from_env()
app = create_app(settings)


def main() -> None:
    loop_factory = None
    if sys.platform == "win32":
        loop_factory = lambda: asyncio.SelectorEventLoop(selectors.SelectSelector())
    uvicorn.run(
        "services.work.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        loop=loop_factory,
    )


if __name__ == "__main__":
    main()
