"""统一 LLM 与 Embedding 调用工厂。"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

import httpx

from app.core.errors import AppError
from app.core.config import get_settings
from app.core.request_context import get_request_id

_llm_semaphore: asyncio.Semaphore | None = None
_circuit_open_until: float = 0.0
_recent_failures: list[float] = []


@dataclass(frozen=True, slots=True)
class LLMFactory:
    """封装 Chat Completion 与 Embedding 调用。"""

    api_key: str
    base_url: str
    chat_model: str
    embedding_model: str

    @classmethod
    def from_settings(cls) -> "LLMFactory":
        settings = get_settings()
        return cls(
            api_key=settings.dashscope_api_key,
            base_url=settings.openai_base_url.rstrip("/"),
            chat_model=settings.qa_chat_model,
            embedding_model=settings.qa_embedding_model,
        )

    @staticmethod
    def _pick_chat_model() -> str:
        settings = get_settings()
        gray = max(0, min(100, int(settings.llm_gray_percent)))
        if gray <= 0:
            return settings.qa_chat_model
        request_id = get_request_id() or str(time.time_ns())
        token = hashlib.sha1(request_id.encode("utf-8")).hexdigest()
        bucket = int(token[:4], 16) % 100
        return settings.llm_gray_chat_model if bucket < gray else settings.qa_chat_model

    async def embed_text(self, text: str) -> list[float]:
        payload = {"model": self.embedding_model, "input": text}
        response = await self._post_json("/embeddings", payload)
        vector = response["data"][0]["embedding"]
        return [float(v) for v in vector]

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        chat_model = self._pick_chat_model()
        payload = {
            "model": chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        }
        response = await self._post_json("/chat/completions", payload)
        return str(response["choices"][0]["message"]["content"]).strip()

    async def chat_stream(self, system_prompt: str, user_prompt: str) -> AsyncIterator[str]:
        """基于上游流式接口返回增量 token。"""
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required for QA agent.")

        settings = get_settings()
        global _llm_semaphore, _circuit_open_until, _recent_failures
        if _llm_semaphore is None:
            _llm_semaphore = asyncio.Semaphore(max(1, int(settings.llm_concurrency)))

        now = time.time()
        if now < _circuit_open_until:
            raise AppError(
                code="CIRCUIT_OPEN",
                message="LLM upstream circuit is open; failing fast.",
                status_code=503,
            )

        chat_model = self._pick_chat_model()
        payload = {
            "model": chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }

        last_exc: Exception | None = None
        for attempt in range(max(1, int(settings.llm_max_retries)) + 1):
            try:
                async with _llm_semaphore:
                    async with httpx.AsyncClient(timeout=float(settings.llm_timeout_seconds)) as client:
                        async with client.stream(
                            "POST",
                            f"{self.base_url}/chat/completions",
                            json=payload,
                            headers=headers,
                        ) as resp:
                            resp.raise_for_status()
                            _recent_failures = [t for t in _recent_failures if now - t < 60.0]
                            async for raw_line in resp.aiter_lines():
                                line = raw_line.strip()
                                if not line or not line.startswith("data:"):
                                    continue
                                content = line[5:].strip()
                                if content == "[DONE]":
                                    return
                                try:
                                    chunk = json.loads(content)
                                except json.JSONDecodeError:
                                    continue
                                delta = (
                                    chunk.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if delta:
                                    yield str(delta)
                            return
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                _recent_failures.append(time.time())
                _recent_failures = [t for t in _recent_failures if time.time() - t < 60.0]
                if len(_recent_failures) >= int(settings.llm_circuit_fail_threshold):
                    _circuit_open_until = time.time() + float(settings.llm_circuit_open_seconds)
                if attempt < int(settings.llm_max_retries):
                    await asyncio.sleep(float(settings.llm_retry_backoff_seconds) * (attempt + 1))

        raise AppError(
            code="UPSTREAM_LLM_ERROR",
            message=f"LLM stream request failed after retries: {type(last_exc).__name__}",
            status_code=503,
            details=str(last_exc) if last_exc else None,
        )

    async def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required for QA agent.")

        settings = get_settings()
        global _llm_semaphore, _circuit_open_until, _recent_failures
        if _llm_semaphore is None:
            _llm_semaphore = asyncio.Semaphore(max(1, int(settings.llm_concurrency)))

        now = time.time()
        if now < _circuit_open_until:
            raise AppError(
                code="CIRCUIT_OPEN",
                message="LLM upstream circuit is open; failing fast.",
                status_code=503,
            )

        headers = {"Authorization": f"Bearer {self.api_key}"}
        last_exc: Exception | None = None
        for attempt in range(max(1, int(settings.llm_max_retries)) + 1):
            try:
                async with _llm_semaphore:
                    async with httpx.AsyncClient(timeout=float(settings.llm_timeout_seconds)) as client:
                        resp = await client.post(
                            f"{self.base_url}{path}",
                            json=payload,
                            headers=headers,
                        )
                        resp.raise_for_status()
                        _recent_failures = [t for t in _recent_failures if now - t < 60.0]
                        return dict(resp.json())
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                _recent_failures.append(time.time())
                _recent_failures = [t for t in _recent_failures if time.time() - t < 60.0]
                if len(_recent_failures) >= int(settings.llm_circuit_fail_threshold):
                    _circuit_open_until = time.time() + float(settings.llm_circuit_open_seconds)
                if attempt < int(settings.llm_max_retries):
                    await asyncio.sleep(float(settings.llm_retry_backoff_seconds) * (attempt + 1))

        raise AppError(
            code="UPSTREAM_LLM_ERROR",
            message=f"LLM upstream request failed after retries: {type(last_exc).__name__}",
            status_code=503,
            details=str(last_exc) if last_exc else None,
        )
