import logging
import os

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class XoloBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())

    async def setup_hook(self):
        await self.load_extension(f"{__package__}.cogs.greeting")

        server_id = os.getenv("DISCORD_SERVER_ID")
        if server_id:
            server = discord.Object(id=int(server_id))
            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)
            log.info("Comando /hola publicado en tu servidor al instante")
        else:
            await self.tree.sync()
            log.info("Comando /hola publicado globalmente (puede tardar hasta 1 hora)")

    async def on_ready(self):
        log.info("Conectado como %s en %d servidor(es)", self.user, len(self.guilds))
