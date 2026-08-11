from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.version import APP_VERSION
from app.database.models import (
    AnalysisPlanModel,
    CohortCriterionModel,
    CohortDefinitionModel,
    CohortDefinitionVersionModel,
    CohortRunModel,
    CohortRunStepModel,
    ConceptSetMemberModel,
    ConceptSetModel,
    ConceptSetTerminologyRefModel,
    ConceptSetVersionModel,
    DataQualityFindingModel,
    DataQualityRunModel,
    OutcomeDefinitionModel,
    ResearchAnalysisRunModel,
    ResearchPackageModel,
    ResearchSnapshotModel,
    ResearchStudyModel,
    StudyProtocolVersionModel,
    TerminologyReleaseModel,
    UserModel,
)
from app.schemas.research_schema import (
    CohortDefinitionCreate,
    CohortReviewRequest,
    CohortRunRequest,
    ConceptSetCreate,
    ConceptSetReviewRequest,
    OutcomeDefinitionCreate,
    OutcomeReviewRequest,
    ResearchReviewRequest,
    ResearchStudyCreate,
    StudyProtocolVersionCreate,
)
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256, json_compatible
from app.services.cohort_dsl import (
    ENGINE_VERSION,
    CohortDSLValidationError,
    CohortDSLValidator,
    DeterministicCohortEngine,
)


class ResearchError(ValueError):
    pass


class ResearchConflict(ResearchError):
    pass


class ResearchNotFound(ResearchError):
    pass


class ResearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_study(
        self,
        payload: ResearchStudyCreate,
        actor: UserModel,
    ) -> ResearchStudyModel:
        study = ResearchStudyModel(
            institution_id=actor.institution_id,
            title=payload.title,
            slug=payload.slug,
            description=payload.description,
            research_question=payload.research_question,
            objective=payload.objective,
            design=payload.design,
            status="draft",
            owner_user_id=actor.id,
            demo_only=True,
            data_source_classification=payload.data_source_classification,
        )
        self.db.add(study)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise ResearchConflict("Slug de estudo já existe na instituição.") from exc
        self._audit(actor, "study.create", "research_study", study.id, "draft")
        return study

    def list_studies(
        self,
        actor: UserModel,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[ResearchStudyModel]:
        return list(
            self.db.scalars(
                select(ResearchStudyModel)
                .where(ResearchStudyModel.institution_id == actor.institution_id)
                .order_by(ResearchStudyModel.updated_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )

    def study(self, study_id: str, actor: UserModel) -> ResearchStudyModel:
        study = self.db.get(ResearchStudyModel, study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo não encontrado.")
        return study

    def create_protocol_version(
        self,
        study_id: str,
        payload: StudyProtocolVersionCreate,
        actor: UserModel,
    ) -> StudyProtocolVersionModel:
        study = self.study(study_id, actor)
        definition = payload.model_dump(mode="json")
        version_number = self._next_version(StudyProtocolVersionModel, "study_id", study.id)
        version = StudyProtocolVersionModel(
            study_id=study.id,
            institution_id=study.institution_id,
            version=version_number,
            **json_compatible(definition),
            status="draft",
            definition_hash=canonical_sha256(definition),
            authored_by_user_id=actor.id,
        )
        self.db.add(version)
        self.db.flush()
        self._audit(
            actor,
            "protocol.version.create",
            "study_protocol_version",
            version.id,
            "draft",
            {"study_id": study.id, "definition_hash": version.definition_hash},
        )
        return version

    def review_protocol(
        self,
        version_id: str,
        payload: ResearchReviewRequest,
        actor: UserModel,
    ) -> StudyProtocolVersionModel:
        version = self._protocol(version_id, actor)
        if version.authored_by_user_id == actor.id:
            raise ResearchError("A revisão do protocolo deve ser independente do autor.")
        if version.status in {"reviewed_demo", "superseded", "archived"}:
            raise ResearchConflict("Versão imutável ou encerrada.")
        version.status = payload.decision
        version.reviewed_by_user_id = actor.id
        version.reviewed_at = datetime.now(UTC)
        if payload.decision == "reviewed_demo":
            study = self.study(version.study_id, actor)
            previous_id = study.current_protocol_version_id
            if previous_id and previous_id != version.id:
                previous = self.db.get(StudyProtocolVersionModel, previous_id)
                if previous is not None and previous.status == "reviewed_demo":
                    previous.status = "superseded"
            study.current_protocol_version_id = version.id
            study.status = "protocol_reviewed_demo"
        self.db.flush()
        self._audit(
            actor,
            "protocol.review",
            "study_protocol_version",
            version.id,
            payload.decision,
            {"note": payload.note},
        )
        return version

    def create_concept_set(
        self,
        payload: ConceptSetCreate,
        actor: UserModel,
    ) -> dict:
        definition = payload.model_dump(mode="json")
        release_ids = definition.pop("terminology_release_ids")
        releases = []
        for release_id in sorted(set(release_ids)):
            release = self.db.get(TerminologyReleaseModel, release_id)
            if release is None or release.institution_id != actor.institution_id:
                raise ResearchError("Terminology release inexistente ou cross-tenant.")
            releases.append(release)
        definition["terminology_release_refs"] = [
            {"id": item.id, "version": item.version, "content_hash": item.content_hash}
            for item in releases
        ]
        concept_set = ConceptSetModel(
            institution_id=actor.institution_id,
            name=payload.name,
            domain=payload.domain,
            status="terminology_matched",
            owner_user_id=actor.id,
        )
        self.db.add(concept_set)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise ResearchConflict("Concept set já existe na instituição.") from exc
        version = ConceptSetVersionModel(
            concept_set_id=concept_set.id,
            institution_id=actor.institution_id,
            version=1,
            status="terminology_matched",
            terminology_versions=payload.terminology_versions,
            include_descendants=payload.include_descendants,
            source_refs=payload.source_refs,
            license_metadata=json_compatible(payload.license_metadata),
            provenance=json_compatible(payload.provenance),
            definition_hash=canonical_sha256(definition),
            authored_by_user_id=actor.id,
        )
        self.db.add(version)
        self.db.flush()
        for member in payload.members:
            self.db.add(
                ConceptSetMemberModel(
                    concept_set_version_id=version.id,
                    **member.model_dump(),
                )
            )
        for release in releases:
            ref_basis = {
                "concept_set_version_id": version.id,
                "release_id": release.id,
                "release_hash": release.content_hash,
                "mapping_hashes": [],
                "expansion_policy": "descendants" if payload.include_descendants else "none",
            }
            self.db.add(
                ConceptSetTerminologyRefModel(
                    concept_set_version_id=version.id,
                    release_id=release.id,
                    mapping_hashes=[],
                    expansion_policy=ref_basis["expansion_policy"],
                    content_hash=canonical_sha256(ref_basis),
                )
            )
        concept_set.current_version_id = version.id
        self.db.flush()
        self._audit(
            actor,
            "concept_set.create",
            "concept_set",
            concept_set.id,
            version.status,
            {"version_id": version.id, "definition_hash": version.definition_hash},
        )
        return self.concept_set_detail(concept_set.id, actor)

    def list_concept_sets(
        self,
        actor: UserModel,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[dict]:
        rows = list(
            self.db.scalars(
                select(ConceptSetModel)
                .where(ConceptSetModel.institution_id == actor.institution_id)
                .order_by(ConceptSetModel.name)
                .offset(offset)
                .limit(limit)
            )
        )
        return [self.concept_set_detail(row.id, actor) for row in rows]

    def concept_set_detail(self, concept_set_id: str, actor: UserModel) -> dict:
        concept_set = self.db.get(ConceptSetModel, concept_set_id)
        if concept_set is None or concept_set.institution_id != actor.institution_id:
            raise ResearchNotFound("Concept set não encontrado.")
        version = (
            self.db.get(ConceptSetVersionModel, concept_set.current_version_id)
            if concept_set.current_version_id
            else None
        )
        members = (
            list(
                self.db.scalars(
                    select(ConceptSetMemberModel).where(
                        ConceptSetMemberModel.concept_set_version_id == version.id
                    )
                )
            )
            if version
            else []
        )
        terminology_refs = (
            list(
                self.db.scalars(
                    select(ConceptSetTerminologyRefModel)
                    .where(ConceptSetTerminologyRefModel.concept_set_version_id == version.id)
                    .order_by(ConceptSetTerminologyRefModel.release_id)
                )
            )
            if version
            else []
        )
        return {
            **self._row(concept_set),
            "version": (
                {
                    **self._row(version),
                    "terminology_release_refs": [
                        {
                            "release_id": item.release_id,
                            "mapping_hashes": item.mapping_hashes,
                            "expansion_policy": item.expansion_policy,
                            "content_hash": item.content_hash,
                        }
                        for item in terminology_refs
                    ],
                }
                if version
                else None
            ),
            "members": [self._row(item) for item in members],
        }

    def review_concept_set(
        self,
        version_id: str,
        payload: ConceptSetReviewRequest,
        actor: UserModel,
    ) -> ConceptSetVersionModel:
        version = self._concept_version(version_id, actor)
        if version.authored_by_user_id == actor.id:
            raise ResearchError("A revisão terminológica deve ser independente do autor.")
        allowed_transitions = {
            "terminology_matched": {"human_reviewed", "rejected"},
            "human_reviewed": {"approved_for_demo_study", "rejected"},
        }
        if payload.decision not in allowed_transitions.get(version.status, set()):
            raise ResearchConflict("Transição de revisão do concept set inválida.")
        version.status = payload.decision
        version.reviewed_by_user_id = actor.id
        version.reviewed_at = datetime.now(UTC)
        concept_set = self.db.get(ConceptSetModel, version.concept_set_id)
        if concept_set is not None:
            concept_set.status = payload.decision
            concept_set.reviewer_user_id = actor.id
        self.db.flush()
        self._audit(
            actor,
            "concept_set.review",
            "concept_set_version",
            version.id,
            payload.decision,
            {"note": payload.note},
        )
        return version

    def create_cohort_version(
        self,
        study_id: str,
        payload: CohortDefinitionCreate,
        actor: UserModel,
    ) -> CohortDefinitionVersionModel:
        study = self.study(study_id, actor)
        try:
            normalized, criteria, cost = CohortDSLValidator(self.db, actor.institution_id).validate(
                payload.definition
            )
        except CohortDSLValidationError as exc:
            raise ResearchError(f"cohort-invalid: {exc}") from exc
        cohort = self.db.scalar(
            select(CohortDefinitionModel).where(
                CohortDefinitionModel.study_id == study.id,
                CohortDefinitionModel.name == payload.name,
            )
        )
        if cohort is None:
            cohort = CohortDefinitionModel(
                study_id=study.id,
                institution_id=study.institution_id,
                name=payload.name,
                status="draft",
                created_by_user_id=actor.id,
            )
            self.db.add(cohort)
            self.db.flush()
        elif cohort.status == "archived":
            raise ResearchConflict("Coorte arquivada não aceita nova versão.")
        version_number = self._next_version(
            CohortDefinitionVersionModel,
            "cohort_definition_id",
            cohort.id,
        )
        version = CohortDefinitionVersionModel(
            cohort_definition_id=cohort.id,
            study_id=study.id,
            institution_id=study.institution_id,
            version=version_number,
            definition=normalized,
            definition_hash=canonical_sha256(normalized),
            status="draft",
            query_cost=cost,
            authored_by_user_id=actor.id,
        )
        self.db.add(version)
        self.db.flush()
        for sequence, criterion in enumerate(criteria, start=1):
            self.db.add(
                CohortCriterionModel(
                    cohort_version_id=version.id,
                    sequence=sequence,
                    group_type=criterion["group"],
                    criterion=criterion["criterion"],
                    operator=criterion["operator"],
                    field=criterion["field"],
                    value={"raw": criterion["value"]},
                    concept_set_version_id=criterion["concept_set_version_id"],
                    window=criterion["window"],
                    criterion_hash=canonical_sha256(criterion),
                )
            )
        self.db.flush()
        self._audit(
            actor,
            "cohort.version.create",
            "cohort_definition_version",
            version.id,
            "draft",
            {"study_id": study.id, "definition_hash": version.definition_hash},
        )
        return version

    def review_cohort(
        self,
        version_id: str,
        payload: CohortReviewRequest,
        actor: UserModel,
    ) -> CohortDefinitionVersionModel:
        version = self._cohort_version(version_id, actor)
        if version.authored_by_user_id == actor.id:
            raise ResearchError("A revisão da coorte deve ser independente do autor.")
        if version.status != "draft":
            raise ResearchConflict("A versão da coorte já foi revisada.")
        version.status = payload.decision
        version.reviewed_by_user_id = actor.id
        version.reviewed_at = datetime.now(UTC)
        cohort = self.db.get(CohortDefinitionModel, version.cohort_definition_id)
        if cohort is not None and payload.decision == "reviewed_demo":
            cohort.current_version_id = version.id
            cohort.status = "reviewed_demo"
        self.db.flush()
        return version

    def create_outcome(
        self,
        study_id: str,
        payload: OutcomeDefinitionCreate,
        actor: UserModel,
    ) -> OutcomeDefinitionModel:
        study = self.study(study_id, actor)
        for version_id in payload.concept_set_version_ids:
            self._concept_version(version_id, actor)
        definition = payload.model_dump(mode="json")
        version_number = (
            int(
                self.db.scalar(
                    select(func.max(OutcomeDefinitionModel.version)).where(
                        OutcomeDefinitionModel.study_id == study.id,
                        OutcomeDefinitionModel.name == payload.name,
                    )
                )
                or 0
            )
            + 1
        )
        outcome = OutcomeDefinitionModel(
            study_id=study.id,
            institution_id=study.institution_id,
            **json_compatible(definition),
            version=version_number,
            review_status="pending_review",
            definition_hash=canonical_sha256(definition),
            authored_by_user_id=actor.id,
        )
        self.db.add(outcome)
        self.db.flush()
        self._audit(
            actor,
            "outcome.create",
            "outcome_definition",
            outcome.id,
            "pending_review",
            {"study_id": study.id, "definition_hash": outcome.definition_hash},
        )
        return outcome

    def review_outcome(
        self,
        outcome_id: str,
        payload: OutcomeReviewRequest,
        actor: UserModel,
    ) -> OutcomeDefinitionModel:
        outcome = self.db.get(OutcomeDefinitionModel, outcome_id)
        if outcome is None or outcome.institution_id != actor.institution_id:
            raise ResearchNotFound("Outcome não encontrado.")
        if outcome.authored_by_user_id == actor.id:
            raise ResearchError("A revisão do outcome deve ser independente do autor.")
        if outcome.review_status != "pending_review":
            raise ResearchConflict("O outcome já foi revisado.")
        outcome.review_status = payload.decision
        outcome.reviewed_by_user_id = actor.id
        outcome.reviewed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            "outcome.review",
            "outcome_definition",
            outcome.id,
            outcome.review_status,
            {"note": payload.note},
        )
        return outcome

    def execute_cohort(
        self,
        version_id: str,
        payload: CohortRunRequest,
        actor: UserModel,
    ) -> CohortRunModel:
        version = self._cohort_version(version_id, actor)
        study = self.study(version.study_id, actor)
        if version.status != "reviewed_demo":
            raise ResearchError("cohort-invalid: versão sem revisão humana.")
        protocol = (
            self._protocol(study.current_protocol_version_id, actor)
            if study.current_protocol_version_id
            else None
        )
        if protocol is None or protocol.status != "reviewed_demo":
            raise ResearchError("cohort-invalid: protocolo revisado ausente.")
        outcome_count = self.db.scalar(
            select(func.count(OutcomeDefinitionModel.id)).where(
                OutcomeDefinitionModel.study_id == study.id,
                OutcomeDefinitionModel.institution_id == actor.institution_id,
            )
        )
        if not outcome_count:
            raise ResearchError("cohort-invalid: outcome versionado ausente.")
        executed_at = datetime.now(UTC)
        try:
            result_count, attrition, analytics = DeterministicCohortEngine(
                self.db, actor.institution_id
            ).execute(version.definition, executed_at=executed_at)
        except CohortDSLValidationError as exc:
            self._audit(
                actor,
                "cohort.run.fail",
                "cohort_definition_version",
                version.id,
                "cohort-invalid",
                {"error_class": type(exc).__name__},
            )
            raise ResearchError(f"cohort-invalid: {exc}") from exc
        source_refs = sorted(
            set(protocol.source_refs or [])
            | set(self._cohort_concept_source_refs(version.definition, actor))
        )
        run_basis = {
            "study_id": study.id,
            "cohort_version_id": version.id,
            "protocol_version_id": protocol.id,
            "data_snapshot_marker": payload.data_snapshot_marker,
            "definition_hash": version.definition_hash,
            "source_version_refs": source_refs,
            "result_count": result_count,
            "attrition": attrition,
            "analytics": analytics,
            "engine_version": ENGINE_VERSION,
            "prescripta_version": APP_VERSION,
        }
        run = CohortRunModel(
            study_id=study.id,
            cohort_version_id=version.id,
            protocol_version_id=protocol.id,
            institution_id=actor.institution_id,
            data_snapshot_marker=payload.data_snapshot_marker,
            executed_at=executed_at,
            executed_by_user_id=actor.id,
            definition_hash=version.definition_hash,
            source_version_refs=source_refs,
            result_count=result_count,
            attrition=attrition,
            analytics=analytics,
            engine_version=ENGINE_VERSION,
            prescripta_version=APP_VERSION,
            status="completed_demo",
            warnings=["Dados sintéticos/demonstrativos; não usar para inferência clínica."],
            run_hash=canonical_sha256(run_basis),
        )
        self.db.add(run)
        self.db.flush()
        for step in attrition:
            self.db.add(
                CohortRunStepModel(
                    cohort_run_id=run.id,
                    sequence=step["sequence"],
                    criterion=step["criterion"],
                    label=step["label"],
                    before_count=step["before_count"],
                    excluded_count=step["excluded_count"],
                    after_count=step["after_count"],
                    criterion_hash=step["criterion_hash"],
                )
            )
        snapshot_payload = {
            "run_basis": run_basis,
            "cohort_definition": version.definition,
            "protocol_definition_hash": protocol.definition_hash,
            "aggregate_only": True,
            "ai_used": False,
        }
        self.db.add(
            ResearchSnapshotModel(
                cohort_run_id=run.id,
                snapshot_type="cohort_run_v1",
                payload=snapshot_payload,
                snapshot_hash=canonical_sha256(snapshot_payload),
            )
        )
        self.db.flush()
        self._audit(
            actor,
            "cohort.run",
            "cohort_run",
            run.id,
            run.status,
            {
                "study_id": study.id,
                "result_count": result_count,
                "run_hash": run.run_hash,
                "data_snapshot_marker": payload.data_snapshot_marker,
            },
        )
        return run

    def list_runs(
        self,
        actor: UserModel,
        study_id: str | None = None,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[CohortRunModel]:
        statement = select(CohortRunModel).where(
            CohortRunModel.institution_id == actor.institution_id
        )
        if study_id:
            self.study(study_id, actor)
            statement = statement.where(CohortRunModel.study_id == study_id)
        statement = statement.order_by(CohortRunModel.executed_at.desc())
        return list(self.db.scalars(statement.offset(offset).limit(limit)))

    def run(self, run_id: str, actor: UserModel) -> CohortRunModel:
        run = self.db.get(CohortRunModel, run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Execução de coorte não encontrada.")
        return run

    def run_snapshot(self, run_id: str, actor: UserModel) -> ResearchSnapshotModel:
        run = self.run(run_id, actor)
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(ResearchSnapshotModel.cohort_run_id == run.id)
        )
        if snapshot is None:
            raise ResearchNotFound("Snapshot de execução não encontrado.")
        return snapshot

    def workspace(self, actor: UserModel) -> dict:
        institution = actor.institution_id
        counts = {
            "studies": self._count(ResearchStudyModel, institution),
            "concept_sets": self._count(ConceptSetModel, institution),
            "cohort_runs": self._count(CohortRunModel, institution),
            "open_data_quality_findings": int(
                self.db.scalar(
                    select(func.count(DataQualityFindingModel.id)).where(
                        DataQualityFindingModel.institution_id == institution,
                        DataQualityFindingModel.status == "open",
                    )
                )
                or 0
            ),
        }
        counts["recent_runs"] = self.list_runs(actor)[:5]
        counts["synthetic_demo_notice"] = (
            "Research/RWE opera exclusivamente sobre dados sintéticos/demonstrativos."
        )
        return counts

    def study_workspace(self, study_id: str, actor: UserModel) -> dict:
        study = self.study(study_id, actor)
        protocols = list(
            self.db.scalars(
                select(StudyProtocolVersionModel)
                .where(StudyProtocolVersionModel.study_id == study.id)
                .order_by(StudyProtocolVersionModel.version.desc())
            )
        )
        cohorts = list(
            self.db.scalars(
                select(CohortDefinitionVersionModel)
                .where(CohortDefinitionVersionModel.study_id == study.id)
                .order_by(CohortDefinitionVersionModel.created_at.desc())
            )
        )
        outcomes = list(
            self.db.scalars(
                select(OutcomeDefinitionModel)
                .where(OutcomeDefinitionModel.study_id == study.id)
                .order_by(OutcomeDefinitionModel.version.desc())
            )
        )
        runs = self.list_runs(actor, study.id, limit=100)
        analysis_plans = list(
            self.db.scalars(
                select(AnalysisPlanModel)
                .where(
                    AnalysisPlanModel.study_id == study.id,
                    AnalysisPlanModel.institution_id == actor.institution_id,
                )
                .order_by(AnalysisPlanModel.version.desc())
            )
        )
        analysis_runs = list(
            self.db.scalars(
                select(ResearchAnalysisRunModel)
                .where(
                    ResearchAnalysisRunModel.study_id == study.id,
                    ResearchAnalysisRunModel.institution_id == actor.institution_id,
                )
                .order_by(ResearchAnalysisRunModel.executed_at.desc())
            )
        )
        packages = list(
            self.db.scalars(
                select(ResearchPackageModel)
                .where(
                    ResearchPackageModel.study_id == study.id,
                    ResearchPackageModel.institution_id == actor.institution_id,
                )
                .order_by(ResearchPackageModel.created_at.desc())
            )
        )
        latest_dq = self.db.scalar(
            select(DataQualityRunModel)
            .where(
                DataQualityRunModel.institution_id == actor.institution_id,
                DataQualityRunModel.study_id == study.id,
                DataQualityRunModel.cohort_run_id == (runs[0].id if runs else None),
                DataQualityRunModel.scope_status == "scoped",
            )
            .order_by(DataQualityRunModel.executed_at.desc())
        )
        concept_versions = sorted(
            {
                str(item.get("concept_set_version_id"))
                for cohort in cohorts
                for item in self._definition_criteria(cohort.definition or {})
                if item.get("concept_set_version_id")
            }
            | {
                version_id
                for outcome in outcomes
                for version_id in outcome.concept_set_version_ids or []
            }
        )
        readiness = [
            {"step": "question", "ready": bool(study.research_question)},
            {
                "step": "protocol",
                "ready": any(item.status == "reviewed_demo" for item in protocols),
            },
            {"step": "cohort", "ready": any(item.status == "reviewed_demo" for item in cohorts)},
            {
                "step": "outcome",
                "ready": any(item.review_status == "reviewed_demo" for item in outcomes),
            },
            {
                "step": "data_quality",
                "ready": latest_dq is not None and not latest_dq.summary.get("analysis_blocked"),
            },
            {
                "step": "analysis_plan",
                "ready": any(item.status == "reviewed_demo" for item in analysis_plans),
            },
            {"step": "results", "ready": bool(analysis_runs)},
            {"step": "evidence_package", "ready": bool(packages)},
        ]
        return {
            "study": study,
            "protocol_versions": protocols,
            "cohort_versions": cohorts,
            "outcomes": outcomes,
            "runs": runs,
            "concept_set_version_ids": concept_versions,
            "analysis_plans": analysis_plans,
            "analysis_runs": analysis_runs,
            "data_quality": (
                {
                    **(latest_dq.summary or {}),
                    "id": latest_dq.id,
                    "cohort_run_id": latest_dq.cohort_run_id,
                    "data_snapshot_marker": latest_dq.data_snapshot_marker,
                    "data_snapshot_hash": latest_dq.data_snapshot_hash,
                    "ruleset_version": latest_dq.ruleset_version,
                    "scope_status": latest_dq.scope_status,
                    "content_hash": latest_dq.content_hash,
                }
                if latest_dq
                else {"status": "not_run"}
            ),
            "readiness": readiness,
            "research_packages": packages,
        }

    def _cohort_concept_source_refs(self, definition: dict, actor: UserModel) -> list[str]:
        sources: list[str] = []
        for criterion in self._definition_criteria(definition):
            version_id = criterion.get("concept_set_version_id")
            if version_id:
                sources.extend(self._concept_version(version_id, actor).source_refs or [])
        return sources

    @staticmethod
    def _definition_criteria(definition: dict) -> list[dict]:
        if "schema_version" not in definition:
            return [item for group in ("all", "exclude") for item in definition.get(group, [])]
        found: list[dict] = []

        def visit(node: dict) -> None:
            if "items" in node:
                for child in node.get("items", []):
                    visit(child)
            elif "criterion" in node:
                found.append(node)

        visit(definition.get("inclusion", {}))
        visit(definition.get("exclusion", {}))
        return found

    def _protocol(self, version_id: str | None, actor: UserModel) -> StudyProtocolVersionModel:
        version = self.db.get(StudyProtocolVersionModel, version_id) if version_id else None
        if version is None or version.institution_id != actor.institution_id:
            raise ResearchNotFound("Versão de protocolo de estudo não encontrada.")
        return version

    def _concept_version(self, version_id: str, actor: UserModel) -> ConceptSetVersionModel:
        version = self.db.get(ConceptSetVersionModel, version_id)
        if version is None or version.institution_id != actor.institution_id:
            raise ResearchNotFound("Concept set/version não encontrado.")
        return version

    def _cohort_version(self, version_id: str, actor: UserModel) -> CohortDefinitionVersionModel:
        version = self.db.get(CohortDefinitionVersionModel, version_id)
        if version is None or version.institution_id != actor.institution_id:
            raise ResearchNotFound("Versão de coorte não encontrada.")
        return version

    def _next_version(self, model, key: str, value: str) -> int:
        return (
            int(
                self.db.scalar(select(func.max(model.version)).where(getattr(model, key) == value))
                or 0
            )
            + 1
        )

    def _count(self, model, institution_id: str) -> int:
        return int(
            self.db.scalar(
                select(func.count(model.id)).where(model.institution_id == institution_id)
            )
            or 0
        )

    @staticmethod
    def _row(model) -> dict:
        return {column.name: getattr(model, column.name) for column in model.__table__.columns}

    def _audit(
        self,
        actor: UserModel,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str,
        details: dict | None = None,
    ) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
        )


def criterion_counts(definition: dict) -> dict[str, int]:
    return dict(
        Counter(
            item["criterion"] for group in ("all", "exclude") for item in definition.get(group, [])
        )
    )
