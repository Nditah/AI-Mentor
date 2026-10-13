"""Model providers sit behind one port. A failure falls through; it does not invent an answer.

Every client gets an explicit timeout and at most one retry, so a hung provider
cannot hold API worker threads for minutes (Runbook HZ-1).
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.core.config import Settings
from app.domain.embeddings import HASH_MODEL, hash_embed

log = logging.getLogger(__name__)
_langfuse: dict[tuple[str, str, str], Any] = {}


class EmbeddingUnavailable(RuntimeError):
    pass


class ProviderRouter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def complete(
        self, *, system: str, messages: list[tuple[str, str]], max_tokens: int = 700
    ) -> str | None:
        attempts = []
        if self.settings.openai_api_key:
            attempts.append(("openai", self.settings.openai_model, self._openai))
        if self.settings.anthropic_api_key:
            attempts.append(("anthropic", self.settings.anthropic_model, self._anthropic))
        if self.settings.gemini_api_key:
            attempts.append(("gemini", self.settings.gemini_model, self._gemini))
        for provider, model, attempt in attempts:
            started = time.monotonic()
            try:
                text = attempt(system, messages, max_tokens)
            except Exception:
                log.warning("model provider %s failed", provider, exc_info=True)
                continue
            if text and text.strip():
                self._trace(provider, model, system, text, time.monotonic() - started)
                return text.strip()
        return None

    def stream(self, *, system: str, messages: list[tuple[str, str]], max_tokens: int = 700):
        """Yield token strings. Falls back to one chunk from `complete` without a stream."""

        if self.settings.openai_api_key:
            try:
                yield from self._openai_stream(system, messages, max_tokens)
                return
            except Exception:
                log.warning("model provider openai stream failed", exc_info=True)
        text = self.complete(system=system, messages=messages, max_tokens=max_tokens)
        if text:
            yield text

    def _openai(self, system: str, messages: list[tuple[str, str]], max_tokens: int) -> str:
        from openai import OpenAI

        client = OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.llm_timeout_seconds,
            max_retries=self.settings.llm_max_retries,
        )
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                *[{"role": role, "content": content} for role, content in messages],
            ],
        )
        return response.choices[0].message.content or ""

    def _openai_stream(self, system: str, messages: list[tuple[str, str]], max_tokens: int):
        from openai import OpenAI

        client = OpenAI(
            api_key=self.settings.openai_api_key,
            timeout=self.settings.llm_timeout_seconds,
            max_retries=self.settings.llm_max_retries,
        )
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            max_tokens=max_tokens,
            stream=True,
            messages=[
                {"role": "system", "content": system},
                *[{"role": role, "content": content} for role, content in messages],
            ],
        )
        for chunk in response:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            text = getattr(delta, "content", None) if delta is not None else None
            if text:
                yield text

    def _anthropic(self, system: str, messages: list[tuple[str, str]], max_tokens: int) -> str:
        from anthropic import Anthropic

        client = Anthropic(
            api_key=self.settings.anthropic_api_key,
            timeout=self.settings.llm_timeout_seconds,
            max_retries=self.settings.llm_max_retries,
        )
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
        from google.genai import types

        client = genai.Client(
            api_key=self.settings.gemini_api_key,
            http_options=types.HttpOptions(timeout=int(self.settings.llm_timeout_seconds * 1000)),
        )
        transcript = "\n".join(f"{role}: {content}" for role, content in messages)
        response = client.models.generate_content(
            model=self.settings.gemini_model,
            contents=transcript,
            config={"system_instruction": system, "max_output_tokens": max_tokens},
        )
        return getattr(response, "text", "") or ""

    def _trace(self, provider: str, model: str, system: str, output: str, seconds: float) -> None:
        """Langfuse is best-effort: a tracing failure never fails a turn."""

        client = langfuse_client(self.settings)
        if client is None:
            return
        try:
            generation = client.start_observation(
                name=f"mentor.{provider}",
                as_type="generation",
                model=model,
                input=system[:500],
                output=output[:2000],
                metadata={"latency_ms": int(seconds * 1000)},
            )
            generation.end()
        except Exception:
            log.warning("langfuse trace skipped", exc_info=True)


def langfuse_client(settings: Settings):  # type: ignore[no-untyped-def]
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    key = (settings.langfuse_public_key, settings.langfuse_secret_key, settings.langfuse_host)
    if key not in _langfuse:
        try:
            from langfuse import Langfuse

            _langfuse[key] = Langfuse(
                public_key=settings.langfuse_public_key,
                secret_key=settings.langfuse_secret_key,
                host=settings.langfuse_host,
                environment=settings.app_env,
            )
        except Exception:
            log.warning("langfuse client could not start", exc_info=True)
            return None
    return _langfuse[key]


def embed_text(settings: Settings, text: str) -> tuple[list[float], str, str]:
    """Embed with the provider model. The hash model is allowed only without Qdrant (RAG-010)."""

    if not settings.openai_api_key:
        if settings.qdrant_enabled:
            raise EmbeddingUnavailable("Qdrant is configured but no embedding provider key is set.")
        return hash_embed(text), "hash", HASH_MODEL
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
    try:
        response = client.embeddings.create(model=settings.embedding_model, input=text)
    except Exception as exc:
        raise EmbeddingUnavailable("The embedding provider did not answer.") from exc
    return list(response.data[0].embedding), "openai", settings.embedding_model


def embed_many(settings: Settings, texts: list[str]) -> tuple[list[list[float]], str, str]:
    """One provider call for a whole document instead of one per chunk."""

    if not texts:
        return [], "hash", HASH_MODEL
    if not settings.openai_api_key:
        vectors = [embed_text(settings, text)[0] for text in texts]
        return vectors, "hash", HASH_MODEL
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.openai_api_key,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )
    vectors: list[list[float]] = []
    try:
        for start in range(0, len(texts), 96):
            batch = texts[start : start + 96]
            response = client.embeddings.create(model=settings.embedding_model, input=batch)
            ordered = sorted(response.data, key=lambda item: item.index)
            vectors.extend(list(item.embedding) for item in ordered)
    except Exception as exc:
        raise EmbeddingUnavailable("The embedding provider did not answer.") from exc
    return vectors, "openai", settings.embedding_model
