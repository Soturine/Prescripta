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

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "excerpt": self.excerpt,
            "score": self.score,
            "matched_terms": self.matched_terms,
            "educational_notice": EDUCATIONAL_NOTICE,
        }


def _documents() -> list[tuple[str, str]]:
    documents: list[tuple[str, str]] = []
    if not KNOWLEDGE_ROOT.exists():
        return documents
    for path in KNOWLEDGE_ROOT.rglob("*.md"):
        documents.append(
            (
                path.relative_to(KNOWLEDGE_ROOT).as_posix(),
                path.read_text(encoding="utf-8"),
            )
        )
    return documents


def retrieve(query_terms: list[str], limit: int = 5) -> list[KnowledgeHit]:
    normalized_terms = normalize_terms(query_terms)
    hits: list[KnowledgeHit] = []
    for source, content in _documents():
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
