from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class ProviderResult:
    provider: str
    model: str
    content: dict[str, Any]
    raw_text: str
    usage: dict[str, Any] = field(default_factory=dict)


class Provider(Protocol):
    def generate_json(self, messages: list[dict[str, str]], model_config: dict[str, Any]) -> ProviderResult:
        ...

