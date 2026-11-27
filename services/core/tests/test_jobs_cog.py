import asyncio

from services.core.app.cogs import jobs


class FakeResponse:
    def __init__(self):
        self.deferred = None

    async def defer(self, **kwargs):
        self.deferred = kwargs


class FakeFollowup:
    def __init__(self):
        self.sent = []

    async def send(self, content=None, **kwargs):
        self.sent.append((content, kwargs))


class FakeInteraction:
    def __init__(self):
        self.response = FakeResponse()
        self.followup = FakeFollowup()


class FakeChannel:
    def __init__(self):
        self.messages = []

    async def send(self, content=None, embed=None):
        self.messages.append((content, embed))


def _offer():
    return {
        "title": "Senior Python Developer",
        "company": "Expert Technology Services",
        "offer_location": "McLean, US",
        "salary": 185000.0,
        "offer_url": "https://example.com/oferta",
    }


def _setup(monkeypatch, channel, refresh, fetch):
    cog = jobs.Jobs(bot=None)
    monkeypatch.setattr(cog, "_refresh", refresh)
    monkeypatch.setattr(cog, "_fetch_offers", fetch)
    monkeypatch.setattr(jobs, "_channel", lambda bot, env_name: channel)
    return cog


def test_ofertas_muestra_guardadas(monkeypatch):
    calls = []
    channel = FakeChannel()
    interaction = FakeInteraction()

    async def refresh():
        calls.append("refresh")

    async def fetch():
        calls.append("fetch")
        return [_offer()], 1

    cog = _setup(monkeypatch, channel, refresh, fetch)
    asyncio.run(jobs.Jobs.ofertas.callback(cog, interaction))

    assert calls == ["fetch"]
    assert interaction.response.deferred == {"ephemeral": True}
    assert interaction.followup.sent == []
    assert len(channel.messages) == 1
    embed = channel.messages[0][1]
    assert embed.title == "Ofertas de empleo · JSearch"
    assert len(embed.fields) == 1
    assert "Senior Python Developer" in embed.fields[0].name
    assert "185,000" in embed.fields[0].value


def test_ofertas_busca_cuando_no_hay_guardadas(monkeypatch):
    calls = []
    channel = FakeChannel()
    interaction = FakeInteraction()
    results = [([], 0), ([_offer()], 1)]

    async def refresh():
        calls.append("refresh")

    async def fetch():
        calls.append("fetch")
        return results.pop(0)

    cog = _setup(monkeypatch, channel, refresh, fetch)
    asyncio.run(jobs.Jobs.ofertas.callback(cog, interaction))

    assert calls == ["fetch", "refresh", "fetch"]
    assert len(channel.messages) == 1
    assert "búsqueda nueva" in channel.messages[0][1].description


def test_ofertas_recientes_siempre_busca(monkeypatch):
    calls = []
    channel = FakeChannel()
    interaction = FakeInteraction()

    async def refresh():
        calls.append("refresh")

    async def fetch():
        calls.append("fetch")
        return [_offer()], 1

    cog = _setup(monkeypatch, channel, refresh, fetch)
    asyncio.run(jobs.Jobs.ofertas_recientes.callback(cog, interaction))

    assert calls == ["refresh", "fetch"]
    assert len(channel.messages) == 1
    assert "búsqueda nueva" in channel.messages[0][1].description
