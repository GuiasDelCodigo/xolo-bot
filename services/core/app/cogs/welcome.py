import discord
from discord import app_commands
from discord.ext import commands

# Nombres de los canales que el bot usa para bienvenidas y despedidas.
WELCOME_CHANNEL = "bienvenida"
GOODBYE_CHANNEL = "despedida"


def _find_channel(guild, name):
    # Busca un canal de texto por nombre. Devuelve None si no existe.
    return discord.utils.get(guild.text_channels, name=name)


def _fallback_channel(guild):
    # Si no existe el canal indicado, usamos el canal del sistema o el primero donde el bot puede escribir.
    me = guild.me
    if guild.system_channel and guild.system_channel.permissions_for(me).send_messages:
        return guild.system_channel
    return next(
        (c for c in guild.text_channels if c.permissions_for(me).send_messages),
        None,
    )


class Welcome(commands.Cog):
    # Se ejecuta cada vez que alguien entra al servidor.
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = _find_channel(member.guild, WELCOME_CHANNEL) or _fallback_channel(member.guild)
        if channel is None:
            return
        await channel.send(f"¡Bienvenido/a {member.mention} al servidor! 🎉")

    # Se ejecuta cada vez que alguien sale o es expulsado del servidor.
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        channel = _find_channel(member.guild, GOODBYE_CHANNEL) or _fallback_channel(member.guild)
        if channel is None:
            return
        # Después de salir ya no se puede mencionar al usuario, así que usamos su nombre.
        await channel.send(f"{member.display_name} se ha ido del servidor. ¡Hasta pronto! 👋")

    # Crea los canales de bienvenida y despedida si todavía no existen.
    @app_commands.command(name="crear_canales", description="Crea los canales de bienvenida y despedida")
    @app_commands.default_permissions(manage_channels=True)
    async def crear_canales(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        creados = []
        try:
            for name in (WELCOME_CHANNEL, GOODBYE_CHANNEL):
                if _find_channel(guild, name) is None:
                    await guild.create_text_channel(name)
                    creados.append(f"#{name}")
        except discord.Forbidden:
            await interaction.followup.send(
                "No tengo permiso para crear canales. Dame el permiso **Gestionar canales**.",
                ephemeral=True,
            )
            return

        if creados:
            await interaction.followup.send(f"Listo, creé: {', '.join(creados)}", ephemeral=True)
        else:
            await interaction.followup.send("Los canales ya existen.", ephemeral=True)


# Required by discord.py to register this cog.
async def setup(bot):
    await bot.add_cog(Welcome())