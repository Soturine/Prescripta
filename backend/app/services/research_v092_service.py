from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.models import (
    AIInteractionModel,
    AnalysisPlanModel,
    CohortRunModel,
    DataQualityFindingModel,
    DataQualityRunModel,
    EvidenceExtractionModel,
    EvidenceSourceModel,
    MedicationSafetyResearchDraftModel,
    OutcomeDefinitionModel,
    PrescriptionAuditModel,
    ResearchComparisonRunModel,
    ResearchPackageModel,
    ResearchQueryPreviewModel,
    ResearchStudyModel,
    TerminologyMappingModel,
    TerminologyReleaseModel,
    UserModel,
)
from app.schemas.research_v092_schema import (
    ComparativeAnalysisRequest,
    MedicationSafetyResearchDraftCreate,
)
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256, json_compatible
from app.services.comparative_analytics_service import ComparativeAnalyticsEngine
from app.services.research_service import ResearchConflict, ResearchNotFound


class ResearchV092Service:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute_comparison(
        self,
        study_id: str,
        payload: ComparativeAnalysisRequest,
        actor: UserModel,
    ) -> ResearchComparisonRunModel:
        study = self._study(study_id, actor)
        exposed = self._cohort_run(payload.exposed_cohort_run_id, study_id, actor)
        comparator = self._cohort_run(payload.comparator_cohort_run_id, study_id, actor)
        if exposed.id == comparator.id:
            raise ResearchConflict("Exposure e comparator exigem cohort runs distintos.")
        if exposed.data_snapshot_marker != payload.dataset_snapshot_marker or (
            comparator.data_snapshot_marker != payload.dataset_snapshot_marker
        ):
            raise ResearchConflict("Cohort runs não pertencem ao snapshot exato informado.")
        expected_groups = {
            "exposed": exposed.result_count,
            "comparator": comparator.result_count,
        }
        actual_groups = {
            group: sum(item.group == group for item in payload.records)
            for group in ("exposed", "comparator")
        }
        if actual_groups != expected_groups:
            raise ResearchConflict(
                "Input sintético não corresponde ao N dos cohort runs exatos."
            )
        dq = self._data_quality(payload.data_quality_run_id, study_id, payload, actor)
        plan = None
        if payload.analysis_plan_id:
            plan = self.db.get(AnalysisPlanModel, payload.analysis_plan_id)
            if (
                plan is None
                or plan.study_id != study_id
                or plan.institution_id != actor.institution_id
            ):
                raise ResearchNotFound("Analysis Plan não encontrado.")
            if plan.status != "reviewed_demo":
                raise ResearchConflict("Analysis Plan exige revisão humana antes da execução.")
        outcomes = []
        for outcome_id in payload.outcome_version_ids:
            outcome = self.db.get(OutcomeDefinitionModel, outcome_id)
            if (
                outcome is None
                or outcome.study_id != study_id
                or outcome.institution_id != actor.institution_id
            ):
                raise ResearchNotFound("Outcome version fora do estudo autorizado.")
            if outcome.review_status != "reviewed_demo":
                raise ResearchConflict("Outcome version exige revisão humana.")
            outcomes.append(
                {
                    "id": outcome.id,
                    "version": outcome.version,
                    "hash": outcome.definition_hash,
                    "terminology_refs": sorted(outcome.concept_set_version_ids or []),
                }
            )
        terminology_refs = []
        for release_id in payload.terminology_release_ids:
            release = self.db.get(TerminologyReleaseModel, release_id)
            if release is None or release.institution_id != actor.institution_id:
                raise ResearchNotFound("Terminology release fora do escopo autorizado.")
            if release.status not in {"active", "imported"}:
                raise ResearchConflict("Terminology release não está ativa/importada.")
            terminology_refs.append(
                {"id": release.id, "version": release.version, "hash": release.content_hash}
            )
        mapping_refs = []
        for mapping_id in payload.mapping_ids:
            mapping = self.db.get(TerminologyMappingModel, mapping_id)
            if mapping is None or mapping.institution_id != actor.institution_id:
                raise ResearchNotFound("Mapping fora do escopo autorizado.")
            if mapping.status != "reviewed":
                raise ResearchConflict("Mapping deve estar reviewed para execução.")
            mapping_refs.append(
                {"id": mapping.id, "version": mapping.version, "hash": mapping.mapping_hash}
            )
        exact_references = {
            "study": {"id": study.id, "status": study.status},
            "analysis_plan": (
                {"id": plan.id, "version": plan.version, "hash": plan.definition_hash}
                if plan
                else None
            ),
            "exposed_cohort_run": self._run_ref(exposed),
            "comparator_cohort_run": self._run_ref(comparator),
            "outcomes": sorted(outcomes, key=lambda item: item["id"]),
            "data_quality": {"id": dq.id, "hash": dq.content_hash},
            "dataset_snapshot": {
                "marker": payload.dataset_snapshot_marker,
                "hash": payload.dataset_snapshot_hash,
            },
            "terminology_releases": sorted(terminology_refs, key=lambda item: item["id"]),
            "mappings": sorted(mapping_refs, key=lambda item: item["id"]),
        }
        input_hash = canonical_sha256(
            {
                "exact_references": exact_references,
                "records": payload.model_dump(mode="json")["records"],
                "configuration": payload.model_dump(exclude={"records"}),
            }
        )
        results, diagnostics, provenance = ComparativeAnalyticsEngine().calculate(payload)
        configuration = json_compatible(payload.model_dump(exclude={"records"}))
        content = {
            "exact_references": exact_references,
            "configuration": configuration,
            "results": results,
            "diagnostics": diagnostics,
            "provenance": provenance,
            "input_hash": input_hash,
        }
        run = ResearchComparisonRunModel(
            study_id=study_id,
            institution_id=actor.institution_id,
            analysis_plan_id=payload.analysis_plan_id,
            exposed_cohort_run_id=exposed.id,
            comparator_cohort_run_id=comparator.id,
            data_quality_run_id=dq.id,
            exact_references=exact_references,
            configuration=configuration,
            results=results,
            diagnostics=diagnostics,
            provenance=provenance,
            exposed_n=exposed.result_count,
            comparator_n=comparator.result_count,
            exposed_events=(
                results["measures"].get("event_counts", {}).get("exposed")
                if results["measures"].get("status") == "computed"
                else None
            ),
            comparator_events=(
                results["measures"].get("event_counts", {}).get("comparator")
                if results["measures"].get("status") == "computed"
                else None
            ),
            input_hash=input_hash,
            content_hash=canonical_sha256(content),
            status="completed_experimental_synthetic",
            synthetic_only=True,
            executed_by_user_id=actor.id,
            executed_at=datetime.now(UTC),
        )
        self.db.add(run)
        self.db.flush()
        self._audit(
            actor,
            "research.comparison.execute",
            "research_comparison_run",
            run.id,
            run.status,
            {
                "study_id": study_id,
                "exposed_n": exposed.result_count,
                "comparator_n": comparator.result_count,
                "psm": payload.psm.enabled,
                "iptw": payload.iptw.enabled,
                "record_level_persisted": False,
            },
        )
        return run

    def comparison(
        self, comparison_id: str, actor: UserModel
    ) -> ResearchComparisonRunModel:
        run = self.db.get(ResearchComparisonRunModel, comparison_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Comparison run não encontrado.")
        return run

    def export_comparison_package(
        self, comparison_id: str, actor: UserModel
    ) -> ResearchPackageModel:
        comparison = self.comparison(comparison_id, actor)
        study = self._study(comparison.study_id, actor)
        ai_interactions = list(
            self.db.scalars(
                select(AIInteractionModel)
                .where(
                    AIInteractionModel.study_id == study.id,
                    AIInteractionModel.institution_id == actor.institution_id,
                )
                .order_by(AIInteractionModel.generated_at, AIInteractionModel.id)
            )
        )
        evidence_ids = sorted(
            {
                source_id
                for interaction in ai_interactions
                for source_id in (interaction.source_ids or [])
            }
        )
        evidence_sources = [
            source
            for source_id in evidence_ids
            if (source := self.db.get(EvidenceSourceModel, source_id)) is not None
            and source.institution_id == actor.institution_id
        ]
        evidence_extractions = list(
            self.db.scalars(
                select(EvidenceExtractionModel).where(
                    EvidenceExtractionModel.institution_id == actor.institution_id,
                    EvidenceExtractionModel.source_id.in_(evidence_ids),
                )
            )
        ) if evidence_ids else []
        query_previews = list(
            self.db.scalars(
                select(ResearchQueryPreviewModel).where(
                    ResearchQueryPreviewModel.study_id == study.id,
                    ResearchQueryPreviewModel.institution_id == actor.institution_id,
                )
            )
        )
        files = {
            "study.json": {
                "id": study.id,
                "title": study.title,
                "research_question": study.research_question,
                "design": study.design,
                "synthetic_only": True,
            },
            "exact-references.json": comparison.exact_references,
            "analysis-plan.json": {
                "id": comparison.analysis_plan_id,
                "configuration": comparison.configuration,
            },
            "comparative-results.json": comparison.results,
            "comparative-diagnostics.json": comparison.diagnostics,
            "method-provenance.json": comparison.provenance,
            "ai-interactions.json": {
                "interactions": [
                    {
                        "id": item.id,
                        "task": item.task_type,
                        "provider": item.provider,
                        "model": item.provider_model_identifier,
                        "template_version": item.prompt_template_version,
                        "schema_version": item.structured_schema_version,
                        "input_hash": item.input_hash,
                        "output_hash": item.output_hash,
                        "source_ids": sorted(item.source_ids or []),
                        "review_status": item.human_review_status,
                        "fallback": item.fallback_used,
                        "policy_version": (item.usage_metadata or {}).get("policy_version"),
                    }
                    for item in ai_interactions
                ],
                "raw_prompts_included": False,
            },
            "evidence.json": {
                "sources": [
                    {
                        "id": item.id,
                        "identifier": item.identifier,
                        "title": item.title,
                        "content_hash": item.content_hash,
                        "license_metadata": item.license_metadata,
                        "review_status": item.review_status,
                    }
                    for item in sorted(evidence_sources, key=lambda value: value.id)
                ],
                "extractions": [
                    {
                        "id": item.id,
                        "source_id": item.source_id,
                        "content_hash": item.content_hash,
                        "schema_version": item.schema_version,
                        "claims": item.claims,
                        "status": item.status,
                    }
                    for item in sorted(evidence_extractions, key=lambda value: value.id)
                ],
            },
            "query-metadata.json": {
                "previews": [
                    {
                        "id": item.id,
                        "query_hash": canonical_sha256(item.normalized_query),
                        "policy": item.policy,
                        "estimated_cost": item.estimated_cost,
                        "status": item.status,
                        "executed": item.executed,
                    }
                    for item in sorted(query_previews, key=lambda value: value.id)
                ],
                "sql_text_included": False,
            },
            "limitations.json": {
                "educational": True,
                "synthetic_only": True,
                "aggregate_only": True,
                "not_epidemiologically_validated": True,
                "not_clinically_validated": True,
                "not_regulatory_validated": True,
                "not_for_patient_care": True,
                "causal_conclusion": False,
                "patient_rows_included": False,
            },
        }
        file_hashes = {name: canonical_sha256(value) for name, value in files.items()}
        manifest = {
            "schema_version": "prescripta-research-package-v3",
            "prescripta_version": "0.9.2",
            "study_id": study.id,
            "analysis_run_id": None,
            "comparison_run_id": comparison.id,
            "comparison_content_hash": comparison.content_hash,
            "aggregate_only": True,
            "synthetic_only": True,
            "method_versions": comparison.provenance,
            "exact_references": comparison.exact_references,
            "files": file_hashes,
        }
        content_hash = canonical_sha256({"manifest": manifest, "files": files})
        existing = self.db.scalar(
            select(ResearchPackageModel).where(
                ResearchPackageModel.comparison_run_id == comparison.id,
                ResearchPackageModel.content_hash == content_hash,
            )
        )
        if existing:
            return existing
        package = ResearchPackageModel(
            study_id=study.id,
            analysis_run_id=None,
            comparison_run_id=comparison.id,
            institution_id=actor.institution_id,
            manifest=manifest,
            files=files,
            content_hash=content_hash,
            aggregate_only=True,
            exported_by_user_id=actor.id,
        )
        self.db.add(package)
        self.db.flush()
        self._audit(
            actor,
            "research.package.export_comparison",
            "research_package",
            package.id,
            "completed",
            {"content_hash": content_hash, "aggregate_only": True, "schema": "v3"},
        )
        return package

    def list_comparisons(
        self, study_id: str, actor: UserModel
    ) -> list[ResearchComparisonRunModel]:
        self._study(study_id, actor)
        return list(
            self.db.scalars(
                select(ResearchComparisonRunModel)
                .where(
                    ResearchComparisonRunModel.study_id == study_id,
                    ResearchComparisonRunModel.institution_id == actor.institution_id,
                )
                .order_by(ResearchComparisonRunModel.executed_at.desc())
            )
        )

    def explore_medication_safety(
        self,
        study_id: str,
        payload: MedicationSafetyResearchDraftCreate,
        actor: UserModel,
    ) -> MedicationSafetyResearchDraftModel:
        self._study(study_id, actor)
        try:
            audit_id = int(payload.source_finding_id)
        except ValueError as exc:
            raise ResearchNotFound("Finding clínico não encontrado.") from exc
        source_audit = self.db.get(PrescriptionAuditModel, audit_id)
        source_user = self.db.get(UserModel, source_audit.user_id) if source_audit else None
        if (
            source_audit is None
            or source_user is None
            or source_user.institution_id != actor.institution_id
        ):
            raise ResearchNotFound("Finding clínico não encontrado.")
        for source_id in payload.source_evidence_ids:
            source = self.db.get(EvidenceSourceModel, source_id)
            if source is None or source.institution_id != actor.institution_id:
                raise ResearchNotFound("Evidence source fora do escopo autorizado.")
        draft = MedicationSafetyResearchDraftModel(
            study_id=study_id,
            institution_id=actor.institution_id,
            **json_compatible(payload.model_dump()),
            status="proposal",
            created_by_user_id=actor.id,
        )
        self.db.add(draft)
        try:
            self.db.flush()
        except IntegrityError as exc:
            raise ResearchConflict("Esse finding já possui draft no estudo.") from exc
        self._audit(
            actor,
            "medication_safety.explore_in_research",
            "medication_safety_research_draft",
            draft.id,
            "proposal",
            {"study_id": study_id, "source_finding_id": payload.source_finding_id},
        )
        return draft

    def _study(self, study_id: str, actor: UserModel) -> ResearchStudyModel:
        study = self.db.get(ResearchStudyModel, study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo não encontrado.")
        return study

    def _cohort_run(
        self, run_id: str, study_id: str, actor: UserModel
    ) -> CohortRunModel:
        run = self.db.get(CohortRunModel, run_id)
        if (
            run is None
            or run.study_id != study_id
            or run.institution_id != actor.institution_id
        ):
            raise ResearchNotFound("Cohort run não encontrado.")
        if run.status != "completed_demo":
            raise ResearchConflict("Cohort run exato não está concluído.")
        return run

    def _data_quality(
        self,
        run_id: str,
        study_id: str,
        payload: ComparativeAnalysisRequest,
        actor: UserModel,
    ) -> DataQualityRunModel:
        run = self.db.get(DataQualityRunModel, run_id)
        if (
            run is None
            or run.institution_id != actor.institution_id
            or run.study_id != study_id
        ):
            raise ResearchNotFound("DQ run não encontrado.")
        if (
            run.status != "completed"
            or run.scope_status != "scoped"
            or run.data_snapshot_marker != payload.dataset_snapshot_marker
            or run.data_snapshot_hash != payload.dataset_snapshot_hash
        ):
            raise ResearchConflict("DQ run não corresponde ao snapshot exato.")
        critical = self.db.scalar(
            select(DataQualityFindingModel.id).where(
                DataQualityFindingModel.run_id == run.id,
                DataQualityFindingModel.severity == "critical",
                DataQualityFindingModel.status == "open",
            )
        )
        if critical is not None:
            raise ResearchConflict("DQ crítico do snapshot bloqueia a comparação.")
        return run

    @staticmethod
    def _run_ref(run: CohortRunModel) -> dict:
        return {
            "id": run.id,
            "cohort_version_id": run.cohort_version_id,
            "definition_hash": run.definition_hash,
            "run_hash": run.run_hash,
            "snapshot_marker": run.data_snapshot_marker,
            "n": run.result_count,
        }

    @staticmethod
    def _audit(
        actor: UserModel,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str,
        details: dict,
    ) -> None:
        # The session is attached to actor through SQLAlchemy; use an explicit service session.
        session = Session.object_session(actor)
        if session is None:
            return
        AuditService(session).record_action(
            user=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details,
        )
