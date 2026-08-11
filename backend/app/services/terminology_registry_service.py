from __future__ import annotations

import base64
import csv
import io
import zipfile
from datetime import UTC, date, datetime
from pathlib import PurePosixPath
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database.models import (
    TerminologyConceptModel,
    TerminologyImportRunModel,
    TerminologyMappingModel,
    TerminologyReleaseModel,
    TerminologySourceModel,
    UserModel,
)
from app.schemas.terminology_schema import (
    TerminologyImportRequest,
    TerminologyMappingCreate,
    TerminologyMappingReview,
    TerminologyReleaseCreate,
    TerminologySourceCreate,
)
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256
from app.services.normalizer import normalize_text

MAX_IMPORT_BYTES = 5_000_000
MAX_UNCOMPRESSED_BYTES = 20_000_000
MAX_ROWS = 50_000
MAX_ARCHIVE_ENTRIES = 4
MAX_COMPRESSION_RATIO = 100
REQUIRED_COLUMNS = {"source_code", "display", "domain", "standard_status"}
ALLOWED_STANDARD_STATUS = {"source", "standard", "classification"}
ALLOWED_DOMAINS = {
    "Person",
    "Visit",
    "Condition",
    "Drug",
    "Measurement",
    "Procedure",
    "Observation",
    "Unit",
    "Type Concept",
}


class TerminologyError(ValueError):
    pass


class TerminologyRegistryService:
    """Governed terminology metadata, imports, lookup, mapping review and drift."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_source(
        self, payload: TerminologySourceCreate, actor: UserModel
    ) -> TerminologySourceModel:
        existing = self.db.scalar(
            select(TerminologySourceModel).where(
                TerminologySourceModel.institution_id == actor.institution_id,
                TerminologySourceModel.canonical_system == payload.canonical_system,
            )
        )
        if existing:
            raise TerminologyError("Canonical system já registrado neste tenant.")
        source = TerminologySourceModel(
            institution_id=actor.institution_id,
            created_by_user_id=actor.id,
            **payload.model_dump(),
        )
        self.db.add(source)
        self.db.flush()
        self._audit(actor, "terminology.source.create", "terminology_source", source.id, {})
        return source

    def list_sources(self, actor: UserModel) -> list[TerminologySourceModel]:
        return list(
            self.db.scalars(
                select(TerminologySourceModel)
                .where(TerminologySourceModel.institution_id == actor.institution_id)
                .order_by(TerminologySourceModel.public_name, TerminologySourceModel.id)
            )
        )

    def create_release(
        self,
        source_id: str,
        payload: TerminologyReleaseCreate,
        actor: UserModel,
    ) -> TerminologyReleaseModel:
        source = self._source(source_id, actor)
        if payload.requires_license and payload.license_status == "authorized":
            raise TerminologyError(
                "Autorização de licença não pode ser autodeclarada na criação da release."
            )
        basis = {"source_id": source.id, **payload.model_dump(mode="json")}
        release = TerminologyReleaseModel(
            source_id=source.id,
            institution_id=actor.institution_id,
            status="configured",
            content_hash=canonical_sha256(basis),
            **payload.model_dump(),
        )
        self.db.add(release)
        self.db.flush()
        self._audit(
            actor,
            "terminology.release.create",
            "terminology_release",
            release.id,
            {"version": release.version, "license_status": release.license_status},
        )
        return release

    def list_releases(
        self, actor: UserModel, source_id: str | None = None
    ) -> list[TerminologyReleaseModel]:
        statement = select(TerminologyReleaseModel).where(
            TerminologyReleaseModel.institution_id == actor.institution_id
        )
        if source_id:
            statement = statement.where(TerminologyReleaseModel.source_id == source_id)
        return list(
            self.db.scalars(
                statement.order_by(
                    TerminologyReleaseModel.version.desc(), TerminologyReleaseModel.id
                )
            )
        )

    def import_bundle(
        self,
        release_id: str,
        payload: TerminologyImportRequest,
        actor: UserModel,
    ) -> TerminologyImportRunModel:
        release = self._release(release_id, actor)
        if release.requires_license and release.license_status != "authorized":
            raise TerminologyError("License required: conteúdo não pode ser importado.")
        try:
            raw = base64.b64decode(payload.content_base64, validate=True)
        except (ValueError, TypeError) as exc:
            raise TerminologyError("Bundle base64 inválido.") from exc
        if not raw or len(raw) > MAX_IMPORT_BYTES:
            raise TerminologyError("Bundle vazio ou acima do limite de tamanho.")
        raw_hash = self._bytes_hash(raw)
        if raw_hash != release.source_checksum:
            raise TerminologyError("Checksum do bundle difere da release registrada.")
        input_hash = canonical_sha256({"bytes_sha256": raw_hash})
        existing = self.db.scalar(
            select(TerminologyImportRunModel).where(
                TerminologyImportRunModel.release_id == release.id,
                TerminologyImportRunModel.input_hash == input_hash,
                TerminologyImportRunModel.status == "completed",
            )
        )
        if existing:
            return existing
        started = datetime.now(UTC)
        run = TerminologyImportRunModel(
            release_id=release.id,
            institution_id=actor.institution_id,
            input_hash=input_hash,
            artifact_name=PurePosixPath(payload.artifact_name.replace("\\", "/")).name,
            status="running",
            imported_by_user_id=actor.id,
            started_at=started,
        )
        self.db.add(run)
        self.db.flush()
        self._audit(actor, "terminology.import.started", "terminology_import", run.id, {})
        try:
            csv_bytes = self._extract_csv(raw, payload.format)
            rows = self._parse_csv(csv_bytes)
            inserted, skipped, rejected, errors = self._load_rows(release, rows)
            run.inserted_count = inserted
            run.skipped_count = skipped
            run.rejected_count = rejected
            run.error_summary = errors
            run.status = "completed" if rejected == 0 else "completed_with_rejections"
            release.imported_at = datetime.now(UTC)
            release.imported_by_user_id = actor.id
            release.import_run_id = run.id
            release.status = "installed" if inserted or skipped else "configured"
        except Exception as exc:
            run.status = "failed"
            run.rejected_count = 1
            run.error_summary = {"bundle": type(exc).__name__}
            run.completed_at = datetime.now(UTC)
            self.db.flush()
            self._audit(
                actor,
                "terminology.import.failed",
                "terminology_import",
                run.id,
                {"error_class": type(exc).__name__},
            )
            raise
        run.completed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            "terminology.import.completed",
            "terminology_import",
            run.id,
            {
                "inserted": run.inserted_count,
                "skipped": run.skipped_count,
                "rejected": run.rejected_count,
            },
        )
        return run

    def search(
        self,
        actor: UserModel,
        *,
        query: str = "",
        release_id: str | None = None,
        domain: str | None = None,
        standard_status: str | None = None,
        active_only: bool = False,
        offset: int = 0,
        limit: int = 50,
    ) -> dict:
        if limit < 1 or limit > 100 or offset < 0:
            raise TerminologyError("Paginação fora dos limites.")
        statement = select(TerminologyConceptModel).where(
            TerminologyConceptModel.institution_id == actor.institution_id
        )
        count_statement = select(func.count(TerminologyConceptModel.id)).where(
            TerminologyConceptModel.institution_id == actor.institution_id
        )
        filters = []
        normalized = normalize_text(query)
        suggestion_only = False
        if normalized:
            filters.append(
                or_(
                    TerminologyConceptModel.source_code == query,
                    TerminologyConceptModel.normalized_display == normalized,
                    TerminologyConceptModel.normalized_display.like(f"{normalized}%"),
                )
            )
            suggestion_only = len(query) < 3 or not any(
                value == query
                for value in self.db.scalars(
                    select(TerminologyConceptModel.source_code)
                    .where(
                        TerminologyConceptModel.institution_id == actor.institution_id,
                        TerminologyConceptModel.source_code == query,
                    )
                    .limit(1)
                )
            )
        if release_id:
            filters.append(TerminologyConceptModel.release_id == release_id)
        if domain:
            filters.append(TerminologyConceptModel.domain == domain)
        if standard_status:
            filters.append(TerminologyConceptModel.standard_status == standard_status)
        if active_only:
            filters.append(TerminologyConceptModel.invalid_reason.is_(None))
        for condition in filters:
            statement = statement.where(condition)
            count_statement = count_statement.where(condition)
        items = list(
            self.db.scalars(
                statement.order_by(
                    TerminologyConceptModel.source_code,
                    TerminologyConceptModel.id,
                )
                .offset(offset)
                .limit(limit)
            )
        )
        return {
            "items": items,
            "offset": offset,
            "limit": limit,
            "total": int(self.db.scalar(count_statement) or 0),
            "suggestion_only": suggestion_only,
        }

    def propose_mapping(
        self, payload: TerminologyMappingCreate, actor: UserModel
    ) -> TerminologyMappingModel:
        source = self._concept(payload.source_concept_id, actor)
        target = self._concept(payload.target_concept_id, actor)
        if source.id == target.id:
            raise TerminologyError("Source e target devem ser conceitos distintos.")
        if payload.supersedes_mapping_id:
            previous = self._mapping(payload.supersedes_mapping_id, actor)
            family_id = previous.mapping_family_id
            version = previous.version + 1
        else:
            previous = None
            family_id = str(uuid4())
            version = 1
        basis = {
            **payload.model_dump(mode="json"),
            "mapping_family_id": family_id,
            "version": version,
            "source_release_id": source.release_id,
            "target_release_id": target.release_id,
        }
        mapping = TerminologyMappingModel(
            mapping_family_id=family_id,
            institution_id=actor.institution_id,
            version=version,
            mapping_hash=canonical_sha256(basis),
            status="proposed",
            authored_by_user_id=actor.id,
            **payload.model_dump(),
        )
        self.db.add(mapping)
        self.db.flush()
        self._audit(actor, "terminology.mapping.proposed", "terminology_mapping", mapping.id, {})
        return mapping

    def review_mapping(
        self,
        mapping_id: str,
        payload: TerminologyMappingReview,
        actor: UserModel,
    ) -> TerminologyMappingModel:
        mapping = self._mapping(mapping_id, actor)
        if mapping.status != "proposed":
            raise TerminologyError("Somente mapping proposed pode ser revisado.")
        if mapping.authored_by_user_id == actor.id:
            raise TerminologyError("Revisão independente obrigatória.")
        source = self._concept(mapping.source_concept_id, actor)
        target = self._concept(mapping.target_concept_id, actor)
        if payload.decision == "approved_for_demo":
            if target.invalid_reason:
                raise TerminologyError("Target inválido/deprecated não pode ser aprovado.")
            if target.standard_status != "standard":
                raise TerminologyError("Target não é Standard Concept.")
            if target.domain != mapping.domain_expectation:
                raise TerminologyError("Domain mismatch bloqueia aprovação.")
            if source.valid_end_date and source.valid_end_date < date.today():
                raise TerminologyError("Source concept expirado.")
        mapping.status = payload.decision
        mapping.reviewed_by_user_id = actor.id
        mapping.reviewed_at = datetime.now(UTC)
        mapping.review_note = payload.note
        self.db.flush()
        self._audit(
            actor,
            "terminology.mapping.reviewed",
            "terminology_mapping",
            mapping.id,
            {"decision": payload.decision},
        )
        return mapping

    def list_mappings(
        self, actor: UserModel, *, status: str | None = None
    ) -> list[TerminologyMappingModel]:
        statement = select(TerminologyMappingModel).where(
            TerminologyMappingModel.institution_id == actor.institution_id
        )
        if status:
            statement = statement.where(TerminologyMappingModel.status == status)
        return list(
            self.db.scalars(
                statement.order_by(
                    TerminologyMappingModel.created_at.desc(),
                    TerminologyMappingModel.id,
                )
            )
        )

    def drift(
        self, source_release_id: str, target_release_id: str, actor: UserModel
    ) -> dict:
        self._release(source_release_id, actor)
        self._release(target_release_id, actor)
        source = {
            item.source_code: item
            for item in self.db.scalars(
                select(TerminologyConceptModel).where(
                    TerminologyConceptModel.release_id == source_release_id,
                    TerminologyConceptModel.institution_id == actor.institution_id,
                )
            )
        }
        target = {
            item.source_code: item
            for item in self.db.scalars(
                select(TerminologyConceptModel).where(
                    TerminologyConceptModel.release_id == target_release_id,
                    TerminologyConceptModel.institution_id == actor.institution_id,
                )
            )
        }
        changes = []
        for code in sorted(set(source) | set(target)):
            old, new = source.get(code), target.get(code)
            if old is None:
                status = "mapping_added"
            elif new is None:
                status = "mapping_removed"
            elif not old.invalid_reason and new.invalid_reason:
                status = "source_concept_deprecated"
            elif old.domain != new.domain:
                status = "domain_changed"
            elif old.content_hash == new.content_hash:
                status = "unchanged"
            else:
                status = "target_changed"
            changes.append({"source_code": code, "status": status})
        summary: dict[str, int] = {}
        for item in changes:
            summary[item["status"]] = summary.get(item["status"], 0) + 1
        basis = {
            "source_release_id": source_release_id,
            "target_release_id": target_release_id,
            "changes": changes,
        }
        return {**basis, "summary": summary, "content_hash": canonical_sha256(basis)}

    def _load_rows(
        self, release: TerminologyReleaseModel, rows: list[dict[str, str]]
    ) -> tuple[int, int, int, dict]:
        source = self.db.get(TerminologySourceModel, release.source_id)
        if source is None:
            raise TerminologyError("Source da release não encontrado.")
        inserted = skipped = rejected = 0
        error_categories: dict[str, int] = {}
        for row in rows:
            try:
                code = row["source_code"].strip()
                display = row["display"].strip()
                domain = row["domain"].strip()
                standard_status = row["standard_status"].strip().lower()
                if not code or not display or domain not in ALLOWED_DOMAINS:
                    raise TerminologyError("invalid_required_field")
                if standard_status not in ALLOWED_STANDARD_STATUS:
                    raise TerminologyError("invalid_standard_status")
                omop_raw = row.get("omop_concept_id", "").strip()
                omop_id = int(omop_raw) if omop_raw else None
                if omop_id is not None and source.family != "omop":
                    raise TerminologyError("omop_id_requires_omop_release")
                aliases_raw = row.get("aliases", "").strip()
                aliases = [value.strip() for value in aliases_raw.split("|") if value.strip()]
                concept_basis = {
                    "release_id": release.id,
                    "source_system": source.canonical_system,
                    "source_code": code,
                    "display": display,
                    "aliases": sorted(aliases),
                    "domain": domain,
                    "concept_class": row.get("concept_class") or None,
                    "standard_status": standard_status,
                    "omop_concept_id": omop_id,
                    "valid_start_date": row.get("valid_start_date") or None,
                    "valid_end_date": row.get("valid_end_date") or None,
                    "invalid_reason": row.get("invalid_reason") or None,
                }
                content_hash = canonical_sha256(concept_basis)
                existing = self.db.scalar(
                    select(TerminologyConceptModel).where(
                        TerminologyConceptModel.release_id == release.id,
                        TerminologyConceptModel.source_code == code,
                    )
                )
                if existing:
                    if existing.content_hash != content_hash:
                        raise TerminologyError("immutable_release_conflict")
                    skipped += 1
                    continue
                self.db.add(
                    TerminologyConceptModel(
                        release_id=release.id,
                        institution_id=release.institution_id,
                        source_system=source.canonical_system,
                        source_code=code,
                        display=display,
                        normalized_display=normalize_text(display),
                        aliases=aliases,
                        domain=domain,
                        concept_class=row.get("concept_class") or None,
                        standard_status=standard_status,
                        omop_concept_id=omop_id,
                        valid_start_date=self._optional_date(row.get("valid_start_date")),
                        valid_end_date=self._optional_date(row.get("valid_end_date")),
                        invalid_reason=row.get("invalid_reason") or None,
                        provenance={"import_hash": release.source_checksum},
                        content_hash=content_hash,
                    )
                )
                inserted += 1
            except (KeyError, ValueError, TerminologyError) as exc:
                rejected += 1
                category = str(exc) or type(exc).__name__
                error_categories[category] = error_categories.get(category, 0) + 1
        self.db.flush()
        return inserted, skipped, rejected, error_categories

    @staticmethod
    def _parse_csv(raw: bytes) -> list[dict[str, str]]:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise TerminologyError("Encoding deve ser UTF-8.") from exc
        if "\x00" in text:
            raise TerminologyError("Conteúdo binário não é aceito.")
        reader = csv.DictReader(io.StringIO(text), strict=True)
        if not reader.fieldnames or not REQUIRED_COLUMNS <= set(reader.fieldnames):
            raise TerminologyError("CSV sem colunas obrigatórias.")
        rows = list(reader)
        if not rows or len(rows) > MAX_ROWS:
            raise TerminologyError("Quantidade de linhas fora do limite.")
        return rows

    @staticmethod
    def _extract_csv(raw: bytes, bundle_format: str) -> bytes:
        if bundle_format == "csv":
            return raw
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw))
        except zipfile.BadZipFile as exc:
            raise TerminologyError("ZIP inválido.") from exc
        entries = archive.infolist()
        if not entries or len(entries) > MAX_ARCHIVE_ENTRIES:
            raise TerminologyError("Archive possui quantidade de entries inválida.")
        candidates = []
        total = 0
        for info in entries:
            path = PurePosixPath(info.filename.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or info.is_dir():
                raise TerminologyError("Archive path traversal/diretório rejeitado.")
            if path.suffix.lower() in {".sql", ".exe", ".sh", ".ps1", ".bat", ".js"}:
                raise TerminologyError("Archive contém tipo de arquivo não permitido.")
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise TerminologyError("Archive excede limite descompactado.")
            if info.file_size and info.compress_size == 0:
                raise TerminologyError("Archive com taxa de compressão inválida.")
            if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                raise TerminologyError("Possível decompression bomb.")
            if path.name == "concepts.csv" and len(path.parts) == 1:
                candidates.append(info)
        if len(candidates) != 1:
            raise TerminologyError("ZIP deve conter exatamente concepts.csv na raiz.")
        return archive.read(candidates[0])

    def _source(self, source_id: str, actor: UserModel) -> TerminologySourceModel:
        source = self.db.get(TerminologySourceModel, source_id)
        if source is None or source.institution_id != actor.institution_id:
            raise TerminologyError("Terminology source não encontrado.")
        return source

    def _release(self, release_id: str, actor: UserModel) -> TerminologyReleaseModel:
        release = self.db.get(TerminologyReleaseModel, release_id)
        if release is None or release.institution_id != actor.institution_id:
            raise TerminologyError("Terminology release não encontrada.")
        return release

    def _concept(self, concept_id: str, actor: UserModel) -> TerminologyConceptModel:
        concept = self.db.get(TerminologyConceptModel, concept_id)
        if concept is None or concept.institution_id != actor.institution_id:
            raise TerminologyError("Terminology concept não encontrado.")
        return concept

    def _mapping(self, mapping_id: str, actor: UserModel) -> TerminologyMappingModel:
        mapping = self.db.get(TerminologyMappingModel, mapping_id)
        if mapping is None or mapping.institution_id != actor.institution_id:
            raise TerminologyError("Terminology mapping não encontrado.")
        return mapping

    @staticmethod
    def _optional_date(value: str | None) -> date | None:
        return date.fromisoformat(value) if value else None

    @staticmethod
    def _bytes_hash(raw: bytes) -> str:
        import hashlib

        return hashlib.sha256(raw).hexdigest()

    def _audit(
        self,
        actor: UserModel,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict,
    ) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status="completed",
            details=details,
        )
