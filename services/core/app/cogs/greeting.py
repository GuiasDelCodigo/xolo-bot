from discord import app_commands
from discord.ext import commands


class Greeting(commands.Cog):
    @app_commands.command(name="hola", description="El bot te saluda")
    async def hola(self, interaction):
        await interaction.response.send_message(f"Hola {interaction.user.display_name}!")


async def setup(bot):
    await bot.add_cog(Greeting())
