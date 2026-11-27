import os

from google import genai

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

SYSTEM_INSTRUCTION = (
    "Responde en español, de forma breve y clara. "
    "Si no tienes información suficiente, dilo."
)


def ask(question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Falta GEMINI_API_KEY en .env."

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=MODEL,
        system_instruction=SYSTEM_INSTRUCTION,
        input=question,
    )
    return interaction.output_text
