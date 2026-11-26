import os

import discord
from dotenv import load_dotenv

from .bot import XoloBot
from .db.session import Database


def main():
    # Load the .env file from the project root.
    load_dotenv()

    token = os.getenv("XOLO_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "No encuentro XOLO_BOT_TOKEN. Copia .env.example a .env en la raíz del proyecto."
        )

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise SystemExit(
            "No encuentro DATABASE_URL. Copiala de services/db/.env.example a tu .env raíz, "
            "o exportala en la terminal antes de correr el bot."
        )

    db = Database(database_url)

    # The prefix is unused (slash commands only), but discord.py requires one.
    bot = XoloBot(command_prefix="!", intents=discord.Intents.default(), db=db)
    bot.run(token)


if __name__ == "__main__":
    main()
