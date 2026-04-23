"""统一 LLM 与 Embedding 调用工厂。"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


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

    async def embed_text(self, text: str) -> list[float]:
        payload = {"model": self.embedding_model, "input": text}
        response = await self._post_json("/embeddings", payload)
        vector = response["data"][0]["embedding"]
        return [float(v) for v in vector]

    async def chat(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.chat_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        response = await self._post_json("/chat/completions", payload)
        return str(response["choices"][0]["message"]["content"]).strip()

    async def _post_json(self, path: str, payload: dict[str, object]) -> dict[str, object]:
        if not self.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is required for QA agent.")

        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.base_url}{path}",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            return dict(resp.json())
