from __future__ import annotations

import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import UTC, date, datetime
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.models import (
    EvidenceAcquisitionRunModel,
    EvidenceSearchPlanModel,
    EvidenceSourceModel,
    ResearchStudyModel,
    UserModel,
)
from app.schemas.evidence_schema import EvidenceSourceCreate
from app.schemas.research_v093_schema import EvidenceSearchPlanCreate
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.evidence_gateway_governance import CACHE, GOVERNOR, POLICIES
from app.services.evidence_service import EvidenceError, EvidenceService
from app.services.outbound_http import SafeOutboundHTTPClient, SafeOutboundHTTPError
from app.services.research_service import ResearchNotFound

EVIDENCE_GATEWAY_VERSION = "evidence-acquisition-v2"
PROVIDER_HOSTS = {
    "pubmed": "eutils.ncbi.nlm.nih.gov",
    "crossref": "api.crossref.org",
    "openalex": "api.openalex.org",
}


class EvidenceAcquisitionError(EvidenceError):
    pass


class EvidenceAcquisitionService:
    def __init__(
        self,
        db: Session,
        *,
        client: SafeOutboundHTTPClient | None = None,
        sleeper=time.sleep,
    ) -> None:
        self.db = db
        self.client = client or SafeOutboundHTTPClient(
            environment=settings.environment,
            allowed_hosts=list(PROVIDER_HOSTS.values()),
            max_response_bytes=1_000_000,
        )
        self.sleeper = sleeper
        self._cache_hits = 0

    def create_plan(
        self, payload: EvidenceSearchPlanCreate, actor: UserModel
    ) -> EvidenceSearchPlanModel:
        study = self.db.get(ResearchStudyModel, payload.study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo não encontrado.")
        self.db.execute(
            select(ResearchStudyModel.id)
            .where(ResearchStudyModel.id == payload.study_id)
            .with_for_update()
        )
        version = (
            int(
                self.db.scalar(
                    select(func.max(EvidenceSearchPlanModel.version)).where(
                        EvidenceSearchPlanModel.institution_id == actor.institution_id,
                        EvidenceSearchPlanModel.study_id == payload.study_id,
                    )
                )
                or 0
            )
            + 1
        )
        body = payload.model_dump(mode="json") | {"version": version}
        plan = EvidenceSearchPlanModel(
            institution_id=actor.institution_id,
            study_id=payload.study_id,
            version=version,
            providers=list(dict.fromkeys(payload.providers)),
            canonical_query=payload.canonical_query,
            provider_queries=payload.provider_queries,
            filters=payload.filters,
            status="draft_needs_review",
            result_count=0,
            identifiers=[],
            content_hash=canonical_sha256(body),
            created_by_user_id=actor.id,
        )
        self.db.add(plan)
        self.db.flush()
        return plan

    def execute(self, plan_id: str, actor: UserModel) -> EvidenceSearchPlanModel:
        plan = self.db.get(EvidenceSearchPlanModel, plan_id)
        if plan is None or plan.institution_id != actor.institution_id:
            raise ResearchNotFound("Evidence Search Plan não encontrado.")
        if plan.status == "executed":
            raise EvidenceAcquisitionError("Plano versionado já executado.")
        all_results: list[dict[str, Any]] = []
        provider_states: list[dict[str, Any]] = []
        for provider in plan.providers:
            started = datetime.now(UTC)
            try:
                results, metadata = self._search_provider(
                    provider,
                    plan.provider_queries.get(provider, plan.canonical_query),
                    plan.filters,
                )
                status = metadata.pop("status", "completed")
            except (EvidenceAcquisitionError, SafeOutboundHTTPError, httpx.HTTPError) as exc:
                results, metadata, status = [], {"error_class": type(exc).__name__}, "unavailable"
            run = EvidenceAcquisitionRunModel(
                plan_id=plan.id,
                institution_id=actor.institution_id,
                provider=provider,
                status=status,
                result_count=len(results),
                provider_metadata=metadata,
                content_hash=canonical_sha256(results),
                started_at=started,
                finished_at=datetime.now(UTC),
            )
            self.db.add(run)
            all_results.extend(results)
            provider_states.append({"provider": provider, "status": status, **metadata})
        deduped = self.deduplicate(all_results)
        source_ids = [self._persist_source(item, actor).id for item in deduped]
        identifiers = [
            {
                "source_id": source_id,
                "provider": item["provider"],
                "doi": item.get("doi"),
                "pmid": item.get("pmid"),
                "pmcid": item.get("pmcid"),
                "openalex_id": item.get("openalex_id"),
                "duplicate_status": item["duplicate_status"],
                "rights_status": item["rights_status"],
            }
            for source_id, item in zip(source_ids, deduped, strict=True)
        ]
        plan.identifiers = identifiers
        plan.result_count = len(identifiers)
        plan.status = "executed"
        plan.executed_at = datetime.now(UTC)
        plan.reviewed_by_user_id = actor.id
        plan.content_hash = canonical_sha256(
            {"plan": plan.content_hash, "identifiers": identifiers, "providers": provider_states}
        )
        self.db.flush()
        AuditService(self.db).record_action(
            user=actor,
            action="evidence.search.execute",
            resource_type="evidence_search_plan",
            resource_id=plan.id,
            status=plan.status,
            details={
                "gateway_version": EVIDENCE_GATEWAY_VERSION,
                "provider_states": provider_states,
                "result_count": plan.result_count,
                "api_keys_persisted": False,
            },
        )
        return plan

    def _search_provider(
        self, provider: str, query: str, filters: dict
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        email = os.getenv("PRESCRIPTA_EVIDENCE_CONTACT_EMAIL", "").strip()
        if provider in {"pubmed", "crossref"} and not email:
            return [], {"status": "configuration_required", "reason": "contact_email"}
        if provider == "pubmed":
            return self._pubmed(query, email, filters)
        if provider == "crossref":
            return self._crossref(query, email, filters)
        if provider == "openalex":
            key = os.getenv("OPENALEX_API_KEY", "").strip()
            if not key:
                return [], {"status": "api_key_required", "credits_consumed": 0}
            return self._openalex(query, key, filters)
        raise EvidenceAcquisitionError("Provider não autorizado.")

    def _pubmed(self, query: str, email: str, filters: dict) -> tuple[list[dict], dict]:
        common = {"db": "pubmed", "tool": "Prescripta", "email": email}
        api_key = os.getenv("NCBI_API_KEY", "").strip()
        if api_key:
            common["api_key"] = api_key
        search = self._json_request(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            {
                **common,
                "term": query,
                "retmode": "json",
                "retmax": min(int(filters.get("limit", 20)), 50),
            },
            credential_hosts={PROVIDER_HOSTS["pubmed"]} if api_key else set(),
        )
        ids = search.get("esearchresult", {}).get("idlist", [])[:50]
        if not ids:
            return [], {"requests": 1, "rate_limit_rps": 2}
        summary = self._json_request(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            {**common, "id": ",".join(ids), "retmode": "json"},
            credential_hosts={PROVIDER_HOSTS["pubmed"]} if api_key else set(),
        )
        structured = self._xml_request(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            {**common, "id": ",".join(ids), "retmode": "xml"},
            credential_hosts={PROVIDER_HOSTS["pubmed"]} if api_key else set(),
        )
        structured_ids: dict[str, dict[str, str]] = {}
        for article in structured.findall(".//PubmedArticle"):
            pmid = article.findtext(".//MedlineCitation/PMID")
            if not pmid:
                continue
            structured_ids[pmid] = {
                str(node.attrib.get("IdType", "")).casefold(): str(node.text or "")
                for node in article.findall(".//PubmedData/ArticleIdList/ArticleId")
            }
        results = []
        for pmid in ids:
            item = summary.get("result", {}).get(str(pmid), {})
            article_ids = {
                entry.get("idtype"): entry.get("value") for entry in item.get("articleids", [])
            }
            article_ids.update(structured_ids.get(str(pmid), {}))
            results.append(
                self._normalized(
                    provider="pubmed",
                    title=item.get("title") or f"PubMed {pmid}",
                    pmid=str(pmid),
                    pmcid=article_ids.get("pmcid"),
                    doi=article_ids.get("doi"),
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    year=str(item.get("pubdate", ""))[:4],
                    authors=[a.get("name", "") for a in item.get("authors", [])],
                    journal=item.get("fulljournalname", ""),
                )
            )
        return results, {"requests": 3, "rate_limit_rps": 2, "history_batching": True}

    def _crossref(self, query: str, email: str, filters: dict) -> tuple[list[dict], dict]:
        body = self._json_request(
            "https://api.crossref.org/works",
            {"query": query, "rows": min(int(filters.get("limit", 20)), 50), "mailto": email},
            headers={"User-Agent": f"Prescripta/0.9.3 (mailto:{email})"},
        )
        items = body.get("message", {}).get("items", [])
        results = [
            self._normalized(
                provider="crossref",
                title=(item.get("title") or ["Untitled"])[0],
                doi=item.get("DOI"),
                url=item.get("URL"),
                year=str(((item.get("published") or {}).get("date-parts") or [[""]])[0][0]),
                authors=[
                    f"{a.get('family', '')}, {a.get('given', '')}" for a in item.get("author", [])
                ],
                journal=((item.get("container-title") or [""])[0]),
                license_metadata={"links": item.get("license", [])},
            )
            for item in items
        ]
        return results, {
            "requests": 1,
            "polite_pool": True,
            "cache": "process_ttl_900s",
            "cache_hits": self._cache_hits,
        }

    def _openalex(self, query: str, key: str, filters: dict) -> tuple[list[dict], dict]:
        body = self._json_request(
            "https://api.openalex.org/works",
            {"search": query, "per-page": min(int(filters.get("limit", 20)), 50), "api_key": key},
            credential_hosts={PROVIDER_HOSTS["openalex"]},
        )
        results = [
            self._normalized(
                provider="openalex",
                title=item.get("display_name") or "Untitled",
                doi=(item.get("doi") or "").removeprefix("https://doi.org/") or None,
                openalex_id=item.get("id"),
                url=item.get("id"),
                year=str(item.get("publication_year") or ""),
                authors=[
                    a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])
                ],
                journal=(
                    ((item.get("primary_location") or {}).get("source") or {}).get(
                        "display_name", ""
                    )
                ),
                license_metadata={"open_access": item.get("open_access", {})},
            )
            for item in body.get("results", [])
        ]
        return results, {
            "requests": 1,
            "authenticated": True,
            "credits_reported": body.get("meta", {}).get("cost_usd"),
        }

    def _json_request(
        self,
        url: str,
        params: dict[str, Any],
        *,
        headers: dict[str, str] | None = None,
        credential_hosts: set[str] | None = None,
    ) -> dict:
        provider = self._provider_for_url(url)
        cache_key = CACHE.key(provider, url, params)
        cached = CACHE.get(cache_key)
        if cached is not None:
            self._cache_hits += 1
            return cached
        response = None
        policy = POLICIES[provider]
        for attempt in range(policy.max_retries + 1):
            semaphore = GOVERNOR.reserve(provider, self.sleeper)
            try:
                response = self.client.request(
                    "GET",
                    url,
                    params=params,
                    headers=headers,
                    timeout_seconds=10,
                    credential_hosts=credential_hosts,
                )
            finally:
                semaphore.release()
            if response.status_code not in {429, 500, 502, 503, 504}:
                break
            if attempt < policy.max_retries:
                self.sleeper(self._retry_delay(response, attempt, policy.retry_after_cap_seconds))
        if response is None or response.status_code >= 400:
            raise EvidenceAcquisitionError("Provider indisponível após retry bounded.")
        content_type = response.headers.get("content-type", "").lower()
        if "json" not in content_type:
            raise EvidenceAcquisitionError("Provider retornou content-type não permitido.")
        try:
            parsed = json.loads(response.content)
            CACHE.put(cache_key, parsed)
            return parsed
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise EvidenceAcquisitionError("Provider retornou JSON inválido.") from exc

    def _xml_request(
        self,
        url: str,
        params: dict[str, Any],
        *,
        credential_hosts: set[str] | None = None,
    ) -> ET.Element:
        provider = self._provider_for_url(url)
        response = None
        policy = POLICIES[provider]
        for attempt in range(policy.max_retries + 1):
            semaphore = GOVERNOR.reserve(provider, self.sleeper)
            try:
                response = self.client.request(
                    "GET",
                    url,
                    params=params,
                    timeout_seconds=10,
                    credential_hosts=credential_hosts,
                )
            finally:
                semaphore.release()
            if response.status_code not in {429, 500, 502, 503, 504}:
                break
            if attempt < policy.max_retries:
                self.sleeper(self._retry_delay(response, attempt, policy.retry_after_cap_seconds))
        if response is None or response.status_code >= 400:
            raise EvidenceAcquisitionError("Provider unavailable after bounded retry.")
        content_type = response.headers.get("content-type", "").lower()
        if "xml" not in content_type:
            raise EvidenceAcquisitionError("Provider returned a disallowed content type.")
        lowered = response.content.lower()
        if b"<!doctype" in lowered or b"<!entity" in lowered:
            raise EvidenceAcquisitionError("XML DTD and entities are blocked.")
        try:
            return ET.fromstring(response.content)
        except ET.ParseError as exc:
            raise EvidenceAcquisitionError("Provider returned invalid XML.") from exc

    @staticmethod
    def _provider_for_url(url: str) -> str:
        for provider, host in PROVIDER_HOSTS.items():
            if f"://{host}/" in url:
                return provider
        raise EvidenceAcquisitionError("Host sem política de rate limit.")

    @staticmethod
    def _retry_delay(response: httpx.Response, attempt: int, cap: float) -> float:
        retry_after = response.headers.get("retry-after", "").strip()
        try:
            if retry_after:
                return min(max(float(retry_after), 0.0), cap)
        except ValueError:
            pass
        return min(0.25 * (2**attempt) + 0.05 * (attempt + 1), cap)

    @staticmethod
    def _normalized(**item: Any) -> dict[str, Any]:
        item.setdefault("doi", None)
        item.setdefault("pmid", None)
        item.setdefault("pmcid", None)
        item.setdefault("openalex_id", None)
        item.setdefault("authors", [])
        item.setdefault("journal", "")
        item.setdefault("year", "")
        item.setdefault("license_metadata", {})
        item["rights_status"] = "metadata_only"
        item["retrieval_source"] = item["provider"]
        item["retrieved_at"] = datetime.now(UTC).isoformat()
        return item

    @staticmethod
    def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: dict[tuple[str, str], dict[str, Any]] = {}
        output: list[dict[str, Any]] = []
        for item in items:
            exact = next(
                (
                    (kind, str(item[kind]).casefold())
                    for kind in ("doi", "pmid", "pmcid", "openalex_id")
                    if item.get(kind)
                ),
                None,
            )
            if exact and exact in seen:
                seen[exact]["duplicate_status"] = "exact_duplicate"
                continue
            heuristic = (
                "heuristic",
                " ".join(str(item.get("title", "")).casefold().split())
                + "|"
                + str(item.get("year", ""))
                + "|"
                + str((item.get("authors") or [""])[0]).casefold()
                + "|"
                + str(item.get("journal", "")).casefold(),
            )
            if not exact and heuristic in seen:
                item["duplicate_status"] = "needs_review"
            else:
                item["duplicate_status"] = "distinct"
            key = exact or heuristic
            seen[key] = item
            output.append(item)
        return output

    def _persist_source(self, item: dict[str, Any], actor: UserModel) -> EvidenceSourceModel:
        identifier = (
            item.get("doi") or item.get("pmid") or item.get("pmcid") or item.get("openalex_id")
        )
        identifier = f"{item['provider']}:{identifier or canonical_sha256(item['title'])[:20]}"
        existing = self.db.scalar(
            select(EvidenceSourceModel).where(
                EvidenceSourceModel.institution_id == actor.institution_id,
                EvidenceSourceModel.identifier == identifier,
            )
        )
        if existing:
            return existing
        return EvidenceService(self.db).create_source(
            EvidenceSourceCreate(
                source_type="observational_study",
                title=item["title"][:300],
                identifier=identifier,
                url=item.get("url"),
                publication_date=(
                    date(int(item["year"]), 1, 1) if str(item.get("year", "")).isdigit() else None
                ),
                access_date=date.today(),
                license_metadata=item["license_metadata"] or {"rights_status": "metadata_only"},
                content_hash=canonical_sha256(item),
                provenance={
                    "gateway_version": EVIDENCE_GATEWAY_VERSION,
                    "provider": item["provider"],
                    "rights_status": item["rights_status"],
                    "metadata_only": True,
                    "ai_generated": False,
                },
            ),
            actor,
        )
