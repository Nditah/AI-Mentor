"""Model providers sit behind one port. A failure falls through; it does not invent an answer."""

from __future__ import annotations

import logging

from app.core.config import Settings
from app.domain.embeddings import HASH_MODEL, hash_embed

log = logging.getLogger(__name__)


class ProviderRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(
        self, *, system: str, messages: list[tuple[str, str]], max_tokens: int = 700
    ) -> str | None:
        attempts = []
        if self.settings.openai_api_key:
            attempts.append(self._openai)
        if self.settings.anthropic_api_key:
            attempts.append(self._anthropic)
        if self.settings.gemini_api_key:
            attempts.append(self._gemini)
        for attempt in attempts:
            try:
                text = attempt(system, messages, max_tokens)
            except Exception:
                log.warning("model provider %s failed", attempt.__name__, exc_info=True)
                continue
            if text and text.strip():
                self._trace(system, text)
                return text.strip()
        return None

    def _openai(self, system: str, messages: list[tuple[str, str]], max_tokens: int) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                *[{"role": role, "content": content} for role, content in messages],
            ],
        )
        return response.choices[0].message.content or ""

    def _anthropic(self, system: str, messages: list[tuple[str, str]], max_tokens: int) -> str:
        from anthropic import Anthropic

        client = Anthropic(api_key=self.settings.anthropic_api_key)
        response = client.messages.create(
            model=self.settings.anthropic_model,
            max_tokens=max_tokens,
            system=system,
            messages=[
                {"role": role, "content": content}
                for role, content in messages
                if role in {"user", "assistant"}
            ],
        )
        blocks = getattr(response, "content", [])
        return "".join(getattr(block, "text", "") for block in blocks)

    def _gemini(self, system: str, messages: list[tuple[str, str]], max_tokens: int) -> str:
        from google import genai

        client = genai.Client(api_key=self.settings.gemini_api_key)
        transcript = "\n".join(f"{role}: {content}" for role, content in messages)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=transcript,
            config={"system_instruction": system, "max_output_tokens": max_tokens},
        )
        return getattr(response, "text", "") or ""

    def _trace(self, system: str, output: str) -> None:
        if not (self.settings.langfuse_public_key and self.settings.langfuse_secret_key):
            return
        try:
            from langfuse import Langfuse

            client = Langfuse(
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
                host=self.settings.langfuse_host,
            )
            trace = getattr(client, "trace", None)
            if trace is None:
                return
            created = client.trace(name="mentor")
            created.generation(name="completion", input=system[:500], output=output[:2000])
        except Exception:
            log.warning("langfuse trace skipped", exc_info=True)


def embed_text(settings: Settings, text: str) -> tuple[list[float], str, str]:
    if not settings.openai_api_key:
        return hash_embed(text), "hash", HASH_MODEL
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=settings.embedding_model, input=text)
    vector = list(response.data[0].embedding)
    return vector, "openai", settings.embedding_model
