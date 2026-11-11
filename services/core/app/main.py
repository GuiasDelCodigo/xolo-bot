import os

import discord
from dotenv import load_dotenv

from .bot import XoloBot


def main():
    # Load the .env file from the project root.
    load_dotenv()

    token = os.getenv("XOLO_BOT_TOKEN")
    if not token:
        raise SystemExit(
            "No encuentro XOLO_BOT_TOKEN. Copia .env.example a .env en la raíz del proyecto."
        )

    # The prefix is unused (slash commands only), but discord.py requires one.
    bot = XoloBot(command_prefix="!", intents=discord.Intents.default())
    bot.run(token)


if __name__ == "__main__":
    main()
