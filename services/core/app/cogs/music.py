import asyncio
import os

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

# Ruta al FFmpeg que viene con el proyecto (Windows). En otros sistemas usa el del PATH.
if os.name == "nt":
    FFMPEG_PATH = os.path.join(
        os.path.dirname(__file__), "..", "bin", "ffmpegWindows", "ffmpeg.exe"
    )
else:
    FFMPEG_PATH = "ffmpeg"

# Opciones para buscar la canción en YouTube (solo obtiene la info, no descarga).
YDL_OPTS = {
    "format": "bestaudio[abr<=96]/bestaudio",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
}

# Opciones para que FFmpeg reproduzca el audio.
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

# La cola de canciones de cada servidor. Clave: ID del servidor. Valor: lista de canciones.
queues = {}


def get_queue(guild_id):
    # Devuelve la cola del servidor, y la crea si todavía no existe.
    return queues.setdefault(guild_id, [])


def _extract(query):
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        return ydl.extract_info(query, download=False)


async def search_track(query):
    # yt-dlp es lento, así que lo corremos en otro hilo para no bloquear el bot.
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _extract, query)


def play_next(voice_client, loop):
    # Toma la siguiente canción de la cola y la reproduce.
    queue = get_queue(voice_client.guild.id)
    if not queue:
        return

    track = queue.pop(0)
    source = discord.FFmpegPCMAudio(track["url"], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)

    # Cuando una canción termina (o se detiene), pasa a la siguiente.
    # Esto se ejecuta en otro hilo, por eso usamos call_soon_threadsafe.
    def when_finished(error):
        if error:
            print(f"Error reproduciendo la canción: {error}")
        loop.call_soon_threadsafe(play_next, voice_client, loop)

    voice_client.play(source, after=when_finished)


class Music(commands.Cog):

    @app_commands.command(name="play", description="Reproduce una canción en el canal de voz")
    @app_commands.describe(nombre_de_la_cancion="Nombre de la canción que quieres escuchar")
    async def play(self, interaction: discord.Interaction, nombre_de_la_cancion: str):
        await interaction.response.defer()

        # Tienes que estar en un canal de voz para que el bot entre.
        voice_state = interaction.user.voice
        if voice_state is None or voice_state.channel is None:
            await interaction.followup.send("Debes estar en un canal de voz para usar este comando.")
            return

        # Conectamos al bot al canal de voz (o lo movemos si está en otro).
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_state.channel.connect()
        elif voice_client.channel != voice_state.channel:
            await voice_client.move_to(voice_state.channel)

        # Buscamos la canción en YouTube.
        result = await search_track(f"ytsearch:{nombre_de_la_cancion}")
        entries = (result or {}).get("entries") or []
        if not entries:
            await interaction.followup.send("No encontré resultados para tu búsqueda.")
            return

        track = {
            "title": entries[0].get("title", "Sin título"),
            "url": entries[0]["url"],
        }

        # La agregamos a la cola.
        queue = get_queue(interaction.guild.id)
        queue.append(track)

        # Si ya hay algo sonando, solo la dejamos en la cola.
        if voice_client.is_playing() or voice_client.is_paused():
            await interaction.followup.send(
                f"Agregada a la cola en la posición {len(queue)}: **{track['title']}**"
            )
        else:
            play_next(voice_client, asyncio.get_running_loop())
            await interaction.followup.send(f"Reproduciendo: **{track['title']}**")

    @app_commands.command(name="pausa", description="Pausa la canción actual")
    async def pausa(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_playing():
            await interaction.response.send_message("No hay nada reproduciéndose.")
            return

        voice_client.pause()
        await interaction.response.send_message("⏸️ Pausado.")

    @app_commands.command(name="reanudar", description="Reanuda la canción pausada")
    async def reanudar(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not voice_client.is_paused():
            await interaction.response.send_message("No hay ninguna canción pausada.")
            return

        voice_client.resume()
        await interaction.response.send_message("▶️ Reanudado.")

    @app_commands.command(name="skip", description="Salta a la siguiente canción de la cola")
    async def skip(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None or not (voice_client.is_playing() or voice_client.is_paused()):
            await interaction.response.send_message("No hay nada reproduciéndose.")
            return

        # stop() hace que se ejecute when_finished, que reproduce la siguiente.
        voice_client.stop()
        await interaction.response.send_message("⏭️ Canción saltada.")

    @app_commands.command(name="stop", description="Detiene la música y vacía la cola")
    async def stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            await interaction.response.send_message("El bot no está en un canal de voz.")
            return

        # Primero vaciamos la cola para que no siga con la siguiente canción.
        get_queue(interaction.guild.id).clear()
        voice_client.stop()
        await interaction.response.send_message("⏹️ Música detenida y cola vacía.")


# Required by discord.py to register this cog. Do not modify.
async def setup(bot):
    await bot.add_cog(Music())
