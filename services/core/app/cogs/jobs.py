import os

import discord
import httpx
from discord import app_commands
from discord.ext import commands

from .welcome import _channel


class Jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = os.getenv("JOBS_API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
        try:
            self.limit = int(os.getenv("JOBS_EMBED_LIMIT", "5"))
        except ValueError:
            self.limit = 5
        self.limit = max(1, min(self.limit, 25))

    @staticmethod
    def _clip(text, max_length):
        value = str(text)
        if len(value) <= max_length:
            return value
        return value[: max_length - 1] + "…"

    async def _request(self, method, path, **kwargs):
        async with httpx.AsyncClient(base_url=self.base_url, timeout=30.0) as client:
            response = await client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()

    async def _refresh(self):
        body = {
            "query": os.getenv(
                "JOBS_DEFAULT_QUERY",
                "developers or programers in Guadalajara Jalisco, Mexico",
            ),
            "category": "DESARROLLO_SOFTWARE",
            "page": 1,
            "num_pages": 1,
            "date_posted": "all",
            "country": "mex",
            "language": "spanish, english",
            "location": "Guadalajara, Jalisco, Mexico",
            "fields": [
                "employer_name",
                "job_publisher",
                "job_title",
                "job_country",
            ],
            "guidelines": [],
        }
        headers = {}
        refresh_token = os.getenv("REFRESH_TOKEN")
        if refresh_token:
            headers["X-Refresh-Token"] = refresh_token
        return await self._request("POST", "/jobs/refresh", json=body, headers=headers)

    async def _fetch_offers(self):
        data = await self._request("GET", "/jobs", params={"limit": self.limit})
        items = data.get("items") or []
        try:
            total = int(data.get("total") or 0)
        except (TypeError, ValueError):
            total = 0
        return items, total

    def _embed(self, items, total, searched):
        source = "búsqueda nueva" if searched else "ofertas guardadas"
        embed = discord.Embed(
            title="Ofertas de empleo · JSearch",
            description=f"{len(items)} de {total} · {source}",
            color=discord.Color.blurple(),
        )
        for index, offer in enumerate(items[: self.limit], 1):
            salary = offer.get("salary")
            if isinstance(salary, (int, float)):
                salary_text = f"{salary:,.0f}"
            else:
                salary_text = "No indicado"
            title = self._clip(offer.get("title") or "Sin título", 250)
            company = self._clip(offer.get("company") or "Sin empresa", 100)
            location = self._clip(offer.get("offer_location") or "No especificada", 100)
            value = (
                f"**Empresa:** {company}\n"
                f"**Ubicación:** {location}\n"
                f"**Salario:** {salary_text}"
            )
            url = offer.get("offer_url")
            if url:
                value += f"\n[Ver oferta]({url})"
            embed.add_field(name=f"{index}. {title}", value=value, inline=False)
        embed.set_footer(text="Xolo Jobs · JSearch")
        return embed

    async def _publish(self, interaction, force_refresh):
        await interaction.response.defer(ephemeral=True)
        channel = _channel(self.bot, "DISCORD_JOBS_CHANNEL_ID")
        if channel is None:
            await interaction.followup.send(
                "El canal de ofertas no existe o el bot no puede escribir en él.",
                ephemeral=True,
            )
            return
        try:
            searched = force_refresh
            if force_refresh:
                await self._refresh()
            items, total = await self._fetch_offers()
            if not items and not force_refresh:
                await self._refresh()
                items, total = await self._fetch_offers()
                searched = True
            if items:
                await channel.send(embed=self._embed(items, total, searched))
            else:
                await channel.send("No hay ofertas disponibles en este momento.")
        except (httpx.HTTPError, ValueError) as exc:
            await interaction.followup.send(
                f"No pude mostrar las ofertas: {exc}", ephemeral=True
            )

    @app_commands.command(
        name="ofertas",
        description="Muestra ofertas guardadas; busca si no hay ninguna",
    )
    async def ofertas(self, interaction: discord.Interaction):
        await self._publish(interaction, force_refresh=False)

    @app_commands.command(
        name="ofertas_recientes",
        description="Busca ofertas nuevas en JSearch y las publica",
    )
    async def ofertas_recientes(self, interaction: discord.Interaction):
        await self._publish(interaction, force_refresh=True)


async def setup(bot):
    await bot.add_cog(Jobs(bot))
