import os

from google import genai

from .knowledge import NO_ANSWER

MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")


def ask(policy: str, chunks: list[dict], question: str) -> str:
    if not chunks:
        return NO_ANSWER

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Falta GEMINI_API_KEY en .env."

    context = "\n\n".join(
        f"[{chunk['file']}]\n{chunk['text']}" for chunk in chunks
    )
    prompt = (
        f"APUNTES DISPONIBLES:\n{context}\n\n"
        f"PREGUNTA: {question}\n\n"
        "Responde en español, máximo 800 caracteres, usando solo los apuntes. "
        f"Si la respuesta no está, di exactamente: {NO_ANSWER}."
    )

    client = genai.Client(api_key=api_key)
    interaction = client.interactions.create(
        model=MODEL,
        system_instruction=policy,
        input=prompt,
        store=False,
    )
    return interaction.output_text
