import asyncio
import os
import tempfile
import uuid

import discord
import yt_dlp
from discord import app_commands
from discord.ext import commands

# Ruta al FFmpeg que viene con el proyecto en services/core/app/bin.
BIN_DIR = os.path.join(os.path.dirname(__file__), "..", "bin")
if os.name == "nt":
    BUNDLED_FFMPEG = os.path.join(BIN_DIR, "ffmpegWindows", "ffmpeg.exe")
else:
    BUNDLED_FFMPEG = os.path.join(BIN_DIR, "ffmpeg", "ffmpeg")

# Si el del proyecto no existe, usa el FFmpeg instalado en el sistema.
if os.path.isfile(BUNDLED_FFMPEG):
    FFMPEG_PATH = BUNDLED_FFMPEG
else:
    FFMPEG_PATH = "ffmpeg"

# Donde se guardan las canciones descargadas temporalmente.
CACHE_DIR = os.path.join(tempfile.gettempdir(), "xolo-music")
os.makedirs(CACHE_DIR, exist_ok=True)

# Opciones para buscar y descargar la canción desde YouTube.
# Descargamos el audio a un archivo local porque FFmpeg no puede abrir
# directamente las URLs HTTPS en algunos servidores (se cae con SIGSEGV),
# ademas de que YouTube exige cabeceras HTTP especificas para esas URLs.
YDL_OPTS = {
    "format": "bestaudio[abr<=96]/bestaudio",
    "noplaylist": True,
    "playlistend": 1,
    "quiet": True,
    "no_warnings": True,
    "noprogress": True,
    "overwrites": True,
}

# Opciones para que FFmpeg reproduzca el audio.
FFMPEG_OPTIONS = {
    "options": "-vn",
}

# La cola de canciones de cada servidor. Clave: ID del servidor. Valor: lista de canciones.
queues = {}


def get_queue(guild_id):
    # Devuelve la cola del servidor, y la crea si todavía no existe.
    return queues.setdefault(guild_id, [])


def _download(query):
    # Nombre único para no sobrescribir una canción que ya está en la cola.
    opts = dict(YDL_OPTS, outtmpl=os.path.join(CACHE_DIR, f"{uuid.uuid4().hex}.%(ext)s"))
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(query, download=True)
        entry = (info.get("entries") or [info])[0]
        return {
            "title": entry.get("title", "Sin título"),
            "path": ydl.prepare_filename(entry),
        }


async def download_track(query):
    # yt-dlp es lento, así que lo corremos en otro hilo para no bloquear el bot.
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _download, query)


def _remove_file(path):
    try:
        os.remove(path)
    except OSError:
        pass


def play_next(voice_client, loop):
    # Toma la siguiente canción de la cola y la reproduce.
    queue = get_queue(voice_client.guild.id)
    if not queue:
        return

    track = queue.pop(0)
    source = discord.FFmpegPCMAudio(track["path"], executable=FFMPEG_PATH, **FFMPEG_OPTIONS)

    # Cuando una canción termina (o se detiene), borramos el archivo temporal
    # y pasamos a la siguiente. Esto corre en otro hilo, por eso usamos
    # call_soon_threadsafe.
    def when_finished(error):
        if error:
            print(f"Error reproduciendo la canción: {error}")
        _remove_file(track["path"])
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

        # Buscamos y descargamos la canción desde YouTube.
        try:
            track = await download_track(f"ytsearch:{nombre_de_la_cancion}")
        except Exception as exc:
            print(f"Error descargando la canción: {exc}")
            if not voice_client.is_playing() and not get_queue(interaction.guild.id):
                await voice_client.disconnect()
            await interaction.followup.send("No pude descargar esa canción. Probá con otra búsqueda.")
            return

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

        # Primero vaciamos la cola para que no siga con la siguiente canción
        # y borramos los archivos temporales pendientes.
        queue = get_queue(interaction.guild.id)
        for pending in queue:
            _remove_file(pending["path"])
        queue.clear()
        voice_client.stop()
        await interaction.response.send_message("⏹️ Música detenida y cola vacía.")


# Required by discord.py to register this cog. Do not modify.
async def setup(bot):
    await bot.add_cog(Music())
