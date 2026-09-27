import logging
import os
from pathlib import Path

from .bot import XoloBot

ENV_PATH = Path(__file__).resolve().parents[3] / ".env"


def load_env():
    if not ENV_PATH.exists():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s")
    load_env()

    token = os.getenv("XOLO_BOT_TOKEN")
    if not token:
        raise SystemExit(f"No encuentro XOLO_BOT_TOKEN. Revisa {ENV_PATH}")

    XoloBot().run(token)


if __name__ == "__main__":
    main()
