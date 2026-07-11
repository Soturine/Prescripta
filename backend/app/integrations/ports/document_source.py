from __future__ import annotations

from typing import Protocol


class DocumentSourcePort(Protocol):
    def get_documents(self) -> list[dict]: ...

    def normalize_documents(self) -> list[dict]: ...
