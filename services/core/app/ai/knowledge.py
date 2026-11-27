import re
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"
POLICY_DIR = KNOWLEDGE_DIR / "politicas"
CONTENT_DIR = KNOWLEDGE_DIR / "conocimientos"

CHUNK_SIZE = 900
OVERLAP = 150

NO_ANSWER = "No tengo información verificada"

DEFAULT_POLICY = (
    "Responde en español y de forma breve. "
    "Usa solo la información de los apuntes disponibles. "
    f"Si no está, di exactamente: {NO_ANSWER}."
)


def load_policy() -> str:
    if not POLICY_DIR.is_dir():
        return DEFAULT_POLICY

    parts = [
        path.read_text(encoding="utf-8").strip()
        for path in sorted(POLICY_DIR.glob("*.md"))
    ]
    parts = [part for part in parts if part]
    return "\n\n".join(parts) if parts else DEFAULT_POLICY


def load_chunks() -> list[dict]:
    if not CONTENT_DIR.is_dir():
        return []

    chunks = []
    for path in sorted(CONTENT_DIR.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for start in range(0, len(text), CHUNK_SIZE - OVERLAP):
            part = text[start:start + CHUNK_SIZE].strip()
            if part:
                chunks.append({"file": path.name, "text": part})
    return chunks


def search(question: str, chunks: list[dict], limit: int = 5) -> list[dict]:
    words = [
        word for word in re.findall(r"\w+", question.lower()) if len(word) > 3
    ]
    if not words:
        return []

    scored = []
    for chunk in chunks:
        text = chunk["text"].lower()
        score = sum(text.count(word) for word in words)
        if score:
            scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]
