import os

import discord
from discord.ext import commands


class XoloBot(commands.Bot):
    async def setup_hook(self):
        # Each file inside cogs/ is a group of commands.
        await self.load_extension("services.core.app.cogs.greeting")

        server_id = os.getenv("DISCORD_SERVER_ID")
        if server_id:
            # With a server ID set, commands appear instantly in that server only.
            server = discord.Object(id=int(server_id))
            self.tree.copy_global_to(guild=server)
            await self.tree.sync(guild=server)
        else:
            # Without a server ID set, commands are published globally (may take up to 1 hour).
            await self.tree.sync()
