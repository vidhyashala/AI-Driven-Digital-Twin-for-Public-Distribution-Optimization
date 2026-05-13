"""Kafka-compatible event bus facade.

The in-memory implementation keeps the prototype runnable without requiring a
Kafka broker. Production deployments can replace this with aiokafka producers
and consumers while preserving the same method signatures.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from app.models import TwinEvent


@dataclass
class KafkaTwinBus:
    """Minimal publish/consume API for twin events."""

    topics: dict[str, deque[TwinEvent]] = field(default_factory=lambda: defaultdict(deque))

    def publish(self, topic: str, event: TwinEvent) -> None:
        self.topics[topic].append(event)

    def consume(self, topic: str, limit: int = 100) -> list[TwinEvent]:
        messages: list[TwinEvent] = []
        queue = self.topics[topic]
        while queue and len(messages) < limit:
            messages.append(queue.popleft())
        return messages
