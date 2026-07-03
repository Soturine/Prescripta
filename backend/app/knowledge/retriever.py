from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.normalizer import normalize_terms

KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1] / "data" / "knowledge_base"
EDUCATIONAL_NOTICE = (
    "Base interna demonstrativa, sem validade clínica completa. Use apenas para explicação."
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
        }


def _documents() -> list[tuple[str, str, dict]]:
    documents: list[tuple[str, str, dict]] = []
    if not KNOWLEDGE_ROOT.exists():
        return documents
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        raw_content = path.read_text(encoding="utf-8")
        metadata, content = _extract_frontmatter(raw_content)
        metadata.setdefault("source_name", path.stem)
        metadata.setdefault("validation_status", "demo")
        metadata.setdefault("evidence_type", "demo_seed")
        metadata.setdefault("jurisdiction", "BR")
        documents.append(
            (
                path.relative_to(KNOWLEDGE_ROOT).as_posix(),
                content,
                metadata,
            )
        )
    return documents


def retrieve(query_terms: list[str], limit: int = 5) -> list[KnowledgeHit]:
    normalized_terms = normalize_terms(query_terms)
    hits: list[KnowledgeHit] = []
    for source, content, metadata in _documents():
        normalized_content_terms = set(normalize_terms(content.split()))
        matched = sorted({term for term in normalized_terms if term in normalized_content_terms})
        if not matched:
            continue
        excerpt = _excerpt(content, matched)
        hits.append(
            KnowledgeHit(
                source=source,
                excerpt=excerpt,
                score=round(len(matched) / max(len(set(normalized_terms)), 1), 2),
                matched_terms=matched,
                metadata=metadata,
            )
        )
    return sorted(hits, key=lambda hit: hit.score, reverse=True)[:limit]


def _excerpt(content: str, matched_terms: list[str]) -> str:
    paragraphs = [paragraph.strip() for paragraph in content.split("\n\n") if paragraph.strip()]
    for paragraph in paragraphs:
        paragraph_terms = set(normalize_terms(paragraph.split()))
        if paragraph_terms & set(matched_terms):
            return paragraph[:700]
    return content[:700]


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
