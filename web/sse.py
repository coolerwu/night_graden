"""SSE 事件总线 / Server-Sent Events Bus

管理每个 task 的实时事件流，供前端通过 SSE 订阅。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator

from utils.logger import get_logger

logger = get_logger("sse")


class EventBus:
    """每个 task 一个独立的 asyncio.Queue，支持多订阅者"""

    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = {}

    def create_stream(self, task_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._queues.setdefault(task_id, []).append(q)
        return q

    async def publish(self, task_id: str, event: dict):
        for q in self._queues.get(task_id, []):
            await q.put(event)

    async def subscribe(self, task_id: str) -> AsyncGenerator[dict, None]:
        q = self.create_stream(task_id)
        try:
            while True:
                event = await q.get()
                yield event
                if event.get("type") == "done":
                    break
        finally:
            queues = self._queues.get(task_id, [])
            if q in queues:
                queues.remove(q)

    def cleanup(self, task_id: str):
        self._queues.pop(task_id, None)


event_bus = EventBus()


async def sse_generator(task_id: str) -> AsyncGenerator[str, None]:
    """将事件转为 SSE 文本格式"""
    async for event in event_bus.subscribe(task_id):
        event_type = event.get("type", "message")
        data = json.dumps(event, ensure_ascii=False, default=str)
        yield f"event: {event_type}\ndata: {data}\n\n"
