import asyncio

import discord
from discord.ext import commands

from services.core.app.ai import gemini, knowledge


class AICog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.policy = knowledge.load_policy()
        self.chunks = knowledge.load_chunks()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.content.strip():
            return

        is_dm = message.guild is None
        mentioned = self.bot.user.mentioned_in(message)
        if not (is_dm or mentioned):
            return

        # In DMs, only answer users who share a server with the bot.
        if is_dm and not any(
            guild.get_member(message.author.id) for guild in self.bot.guilds
        ):
            return

        question = message.content.replace(
            f"<@{self.bot.user.id}>", ""
        ).replace(
            f"<@!{self.bot.user.id}>", ""
        ).strip()

        async with message.channel.typing():
            chunks = knowledge.search(question, self.chunks)
            reply = await asyncio.to_thread(
                gemini.ask, self.policy, chunks, question
            )

        # Discord allows 2000 characters per message.
        for i in range(0, len(reply), 1900):
            await message.channel.send(reply[i:i + 1900])


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AICog(bot))
