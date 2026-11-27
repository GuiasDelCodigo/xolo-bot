from .history import format_history
from .knowledge import NO_ANSWER


def build_prompt(chunks: list[dict], question: str, history: list[dict]) -> str:
    context = "\n\n".join(
        f"[{chunk['file']}]\n{chunk['text']}" for chunk in chunks
    )
    return (
        format_history(history)
        + f"APUNTES DISPONIBLES:\n{context or '(ninguno)'}\n\n"
        + f"PREGUNTA ACTUAL: {question}\n\n"
        + "Responde en español, máximo 800 caracteres. "
        + "Si es un saludo o conversación general, responde con naturalidad. "
        + "Si es una pregunta universitaria, usa los apuntes y la conversación "
        + "reciente solo para entender la pregunta. "
        + "No te presentes ni repitas frases de identidad salvo que te pregunten. "
        + "Si hay información parcial, da la parte verificada y señala qué falta. "
        + f"Si el dato universitario no está en los apuntes, di que no tienes esa informacion."
    )
