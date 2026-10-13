"""Intent routing. Code and papers stay on their own endpoints."""

from __future__ import annotations

from app.domain.catalog import detect_concept
from app.domain.intent import classify_intent


def dispatch(engine: object, user: object, message: str) -> dict:
    intent = classify_intent(message)
    if intent == "career":
        return {"intent": intent, "result": engine.career(user)}  # type: ignore[attr-defined]
    if intent == "plan":
        return {"intent": intent, "result": engine.create_plan(user, message)}  # type: ignore[attr-defined]
    if intent == "quiz":
        concept = detect_concept(message)
        slug = concept.slug if concept is not None else "ai-fundamentals"
        return {"intent": intent, "result": engine.generate_quiz(user, slug, "intermediate")}  # type: ignore[attr-defined]
    if intent == "code":
        return {
            "intent": intent,
            "result": {
                "message": (
                    "Open the coding lab to run or review a file. "
                    "Chat will not execute pasted code."
                )
            },
        }
    if intent == "research":
        return {
            "intent": intent,
            "result": {
                "message": (
                    "Upload the document on the research page. "
                    "Analysis runs only on a file you own."
                )
            },
        }
    return {"intent": "tutor", "result": engine.chat(user, message, None, "socratic")}  # type: ignore[attr-defined]
