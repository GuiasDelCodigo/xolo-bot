import os

import discord
from discord.ext import commands

from .db.session import Database


class XoloBot(commands.Bot):
    def __init__(self, *args, db: Database, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    async def setup_hook(self):
        # Each file inside cogs/ is a group of commands.
        await self.load_extension("services.core.app.cogs.greeting")
        await self.load_extension("services.core.app.cogs.jobs")
        await self.load_extension("services.core.app.cogs.music")
        await self.load_extension("services.core.app.cogs.welcome")

        server_id = os.getenv("DISCORD_SERVER_ID")
        if server_id:
            # With a server ID set, commands appear instantly in that server only.
            server = discord.Object(id=int(server_id))
            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)
        else:
            # Without a server ID set, commands are published globally (may take up to 1 hour).
            await self.tree.sync()

    async def close(self):
        try:
            await super().close()
        finally:
            await self.db.close()
