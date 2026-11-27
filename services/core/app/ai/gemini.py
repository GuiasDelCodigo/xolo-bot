import os

from google import genai

from .prompt import build_prompt

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def ask(
    policy: str,
    chunks: list[dict],
    question: str,
    history: list[dict] | None = None,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Falta GEMINI_API_KEY en .env."

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=MODEL,
        system_instruction=policy,
        input=build_prompt(chunks, question, history or []),
        store=False,
    )
    return interaction.output_text
