"""Redis 会话记忆服务。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.core.config import get_settings


@dataclass(slots=True)
class MemoryService:
    """基于 Redis List 存储多轮对话。"""

    redis: Any
    max_rounds: int = 12

    @classmethod
    def from_settings(cls) -> "MemoryService":
        from redis.asyncio import Redis
        settings = get_settings()
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        return cls(redis=client)

    async def append_turn(self, session_id: str, role: str, content: str) -> None:
        key = self._session_key(session_id)
        await self.redis.rpush(
            key,
            json.dumps({"role": role, "content": content}, ensure_ascii=False),
        )
        await self.redis.ltrim(key, -self.max_rounds * 2, -1)
        await self.redis.expire(key, 86400 * 7)

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        key = self._session_key(session_id)
        rows = await self.redis.lrange(key, 0, -1)
        return [dict(json.loads(item)) for item in rows]

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"qa:memory:{session_id}"
