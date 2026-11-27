import os

import discord
from discord.ext import commands


def _channel(bot, env_name):
    # Returns None when the ID is unset or unusable.
    channel_id = os.getenv(env_name)
    if not channel_id:
        return None
    try:
        channel = bot.get_channel(int(channel_id))
    except ValueError:
        return None
    if not isinstance(channel, discord.TextChannel):
        return None
    perms = channel.permissions_for(channel.guild.me)
    if not (perms.view_channel and perms.send_messages):
        return None
    return channel


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = _channel(self.bot, "DISCORD_WELCOME_CHANNEL_ID")
        if channel is None:
            print("Welcome channel missing or not writable.")
            return
        await channel.send(f"¡Bienvenido/a {member.mention} al servidor! 🎉")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = _channel(self.bot, "DISCORD_GOODBYE_CHANNEL_ID")
        if channel is None:
            print("Goodbye channel missing or not writable.")
            return
        await channel.send(f"{member.display_name} se ha ido del servidor. ¡Hasta pronto! 👋")


async def setup(bot):
    await bot.add_cog(Welcome(bot))
