from dotenv import load_dotenv

load_dotenv()

import uvicorn

from .api import Settings, create_app

settings = Settings.from_env()
app = create_app(settings)


def main() -> None:
    uvicorn.run(
        "services.work.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
