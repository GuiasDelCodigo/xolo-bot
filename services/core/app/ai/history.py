import discord

HISTORY_LIMIT = 20
MAX_CONVERSATIONS = 200


class HistoryStore:
    """In-memory history, separated per channel and per DM user."""

    def __init__(self) -> None:
        self._items: dict[tuple[str, int], list[dict]] = {}

    @staticmethod
    def key_for(message: discord.Message) -> tuple[str, int]:
        if message.guild is None:
            return ("dm", message.author.id)
        return ("channel", message.channel.id)

    def get(self, key: tuple[str, int]) -> list[dict]:
        return self._items.setdefault(key, [])

    def add(self, key: tuple[str, int], question: str, reply: str) -> None:
        history = self.get(key)
        history.extend(
            (
                {"role": "Usuario", "text": question},
                {"role": "Asistente", "text": reply},
            )
        )
        del history[:-HISTORY_LIMIT]

        if len(self._items) > MAX_CONVERSATIONS:
            del self._items[next(iter(self._items))]


def format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = [f"{item['role']}: {item['text']}" for item in history]
    return "CONVERSACIÓN RECIENTE:\n" + "\n".join(lines) + "\n\n"
