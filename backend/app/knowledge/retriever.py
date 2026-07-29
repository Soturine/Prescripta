from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.services.normalizer import normalize_terms

KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"
EDUCATIONAL_NOTICE = (
    "Base interna demonstrativa, sem validade clínica completa. Use apenas para explicação."
)
INDEX_VERSION = "lexical-index-v1"
PROMPT_INJECTION_MARKERS = (
    "ignore previous",
    "ignore todas",
    "system prompt",
    "developer message",
    "assistant:",
)


@dataclass(frozen=True)
class KnowledgeHit:
    source: str
    excerpt: str
    score: float
    matched_terms: list[str]
    metadata: dict

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "source_id": self.metadata.get("source_id"),
            "chunk_id": self.metadata.get("chunk_id"),
            "source_hash": self.metadata.get("source_hash"),
            "index_version": INDEX_VERSION,
            "excerpt": self.excerpt,
            "score": self.score,
            "matched_terms": self.matched_terms,
            "educational_notice": EDUCATIONAL_NOTICE,
            "jurisdiction": self.metadata.get("jurisdiction", "GLOBAL"),
            "source_name": self.metadata.get("source_name", "Base interna demonstrativa"),
            "source_url": self.metadata.get("source_url"),
            "evidence_type": self.metadata.get("evidence_type", "demo_seed"),
            "validation_status": self.metadata.get("validation_status", "demo"),
            "active_ingredient": self.metadata.get("active_ingredient"),
            "commercial_names": self.metadata.get("commercial_names", []),
            "extracted_sections": self.metadata.get("extracted_sections", []),
            "retrieved_at": self.metadata.get("retrieved_at"),
            "version": self.metadata.get("version", "v0.5.0-demo"),
            "valid_until": self.metadata.get("valid_until"),
        }


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    content: str
    terms: frozenset[str]
    metadata: dict


@lru_cache(maxsize=1)
def build_index() -> tuple[KnowledgeChunk, ...]:
    chunks: list[KnowledgeChunk] = []
    seen_hashes: set[str] = set()
    if not KNOWLEDGE_ROOT.exists():
        return ()
    for path in sorted(KNOWLEDGE_ROOT.rglob("*.md")):
        raw_content = path.read_text(encoding="utf-8")
        metadata, content = _extract_frontmatter(raw_content)
        metadata.setdefault("source_name", path.stem)
        metadata.setdefault("validation_status", "demo")
        metadata.setdefault("evidence_type", "demo_seed")
        metadata.setdefault("jurisdiction", "BR")
        source = path.relative_to(KNOWLEDGE_ROOT).as_posix()
        source_hash = hashlib.sha256(raw_content.encode("utf-8")).hexdigest()
        for index, chunk in enumerate(_split_chunks(content), start=1):
            chunk_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            if chunk_hash in seen_hashes or _contains_prompt_injection(chunk):
                continue
            seen_hashes.add(chunk_hash)
            chunk_metadata = {
                **metadata,
                "source_id": f"kb:{source}:{index}",
                "chunk_id": f"{source_hash[:12]}:{index}",
                "source_hash": source_hash,
            }
            chunks.append(
                KnowledgeChunk(
                    source=source,
                    content=chunk,
                    terms=frozenset(normalize_terms(chunk.split())),
                    metadata=chunk_metadata,
                )
            )
    return tuple(chunks)


def retrieve(query_terms: list[str], limit: int = 5) -> list[KnowledgeHit]:
    normalized_terms = normalize_terms(query_terms)
    hits: list[KnowledgeHit] = []
    for chunk in build_index():
        matched = sorted({term for term in normalized_terms if term in chunk.terms})
        if not matched:
            continue
        metadata = dict(chunk.metadata)
        if _is_expired(metadata.get("valid_until")):
            metadata["validation_status"] = "expired"
        hits.append(
            KnowledgeHit(
                source=chunk.source,
                excerpt=chunk.content[:700],
                score=round(len(matched) / max(len(set(normalized_terms)), 1), 2),
                matched_terms=matched,
                metadata=metadata,
            )
        )
    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]


def _split_chunks(content: str, max_chars: int = 1000) -> list[str]:
    paragraphs = [paragraph.strip() for paragraph in content.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def _contains_prompt_injection(content: str) -> bool:
    normalized = " ".join(normalize_terms(content.split()))
    return any(marker in normalized for marker in PROMPT_INJECTION_MARKERS)


def _is_expired(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        return date.fromisoformat(value) < date.today()
    except ValueError:
        return True


def _extract_frontmatter(content: str) -> tuple[dict, str]:
    if not content.startswith("---"):
        return {}, content
    lines = content.splitlines()
    metadata: dict = {}
    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = _parse_metadata_value(value.strip())
    if end_index is None:
        return {}, content
    body = "\n".join(lines[end_index + 1 :]).strip()
    return metadata, body


def _parse_metadata_value(value: str):
    if value.startswith("[") and value.endswith("]"):
        raw_items = value.removeprefix("[").removesuffix("]")
        return [item.strip().strip('"').strip("'") for item in raw_items.split(",") if item.strip()]
    return value.strip('"').strip("'") or None
