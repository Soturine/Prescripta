from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    AnalysisPlanModel,
    CohortRunModel,
    DataQualityFindingModel,
    DataQualityRunModel,
    OutcomeDefinitionModel,
    PatientClinicalTimelineEventModel,
    PatientModel,
    ResearchAnalysisRunModel,
    ResearchPackageModel,
    ResearchSnapshotModel,
    ResearchStudyModel,
    StudyProtocolVersionModel,
    UserModel,
)
from app.schemas.research_schema import AnalysisPlanCreate, ResearchReviewRequest
from app.services.audit_service import AuditService
from app.services.canonical_json import canonical_sha256, json_compatible
from app.services.research_service import ResearchConflict, ResearchError, ResearchNotFound

ALLOWED_METHODS = {
    "population_count",
    "numeric_summary",
    "categorical_distribution",
    "prevalence",
    "baseline_table_1",
    "resource_utilization",
}


class ResearchAnalysisService:
    """Deterministic, descriptive analytics over immutable aggregate cohort snapshots."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_plan(
        self, study_id: str, payload: AnalysisPlanCreate, actor: UserModel
    ) -> AnalysisPlanModel:
        study = self._study(study_id, actor)
        cohort_run = self._cohort_run(payload.cohort_run_id, actor)
        if cohort_run.study_id != study.id or cohort_run.status != "completed_demo":
            raise ResearchError("O plano exige uma coorte concluída do mesmo estudo.")
        methods = set(payload.methods)
        if not methods or not methods <= ALLOWED_METHODS:
            raise ResearchError("O plano contém método não permitido.")
        version = (
            int(
                self.db.scalar(
                    select(func.max(AnalysisPlanModel.version)).where(
                        AnalysisPlanModel.study_id == study.id
                    )
                )
                or 0
            )
            + 1
        )
        definition = payload.model_dump(mode="json")
        plan = AnalysisPlanModel(
            study_id=study.id,
            institution_id=actor.institution_id,
            version=version,
            **json_compatible(definition),
            definition_hash=canonical_sha256(definition),
            status="draft",
            authored_by_user_id=actor.id,
        )
        self.db.add(plan)
        self.db.flush()
        self._audit(
            actor,
            "research.analysis_plan.create",
            "analysis_plan",
            plan.id,
            "draft",
            {"study_id": study.id, "definition_hash": plan.definition_hash},
        )
        return plan

    def list_plans(self, study_id: str, actor: UserModel) -> list[AnalysisPlanModel]:
        self._study(study_id, actor)
        return list(
            self.db.scalars(
                select(AnalysisPlanModel)
                .where(
                    AnalysisPlanModel.study_id == study_id,
                    AnalysisPlanModel.institution_id == actor.institution_id,
                )
                .order_by(AnalysisPlanModel.version.desc())
            )
        )

    def review_plan(
        self, plan_id: str, payload: ResearchReviewRequest, actor: UserModel
    ) -> AnalysisPlanModel:
        plan = self._plan(plan_id, actor)
        if plan.authored_by_user_id == actor.id:
            raise ResearchError("A revisão do plano deve ser independente do autor.")
        if plan.status != "draft":
            raise ResearchConflict("O plano já foi revisado.")
        if payload.decision not in {"reviewed_demo", "archived"}:
            raise ResearchError("Decisão inválida para o plano de análise.")
        plan.status = payload.decision
        plan.reviewed_by_user_id = actor.id
        plan.reviewed_at = datetime.now(UTC)
        self.db.flush()
        self._audit(
            actor,
            "research.analysis_plan.review",
            "analysis_plan",
            plan.id,
            plan.status,
            {"note": payload.note},
        )
        return plan

    def execute(self, plan_id: str, actor: UserModel) -> ResearchAnalysisRunModel:
        plan = self._plan(plan_id, actor)
        if plan.status != "reviewed_demo":
            raise ResearchError("Execução bloqueada: plano sem revisão humana.")
        study = self._study(plan.study_id, actor)
        if not study.demo_only or study.data_source_classification not in {
            "synthetic",
            "internal_demo",
        }:
            raise ResearchError("Execução bloqueada: apenas dados sintéticos são permitidos.")
        cohort_run = self._cohort_run(plan.cohort_run_id or "", actor)
        protocol = self.db.get(StudyProtocolVersionModel, cohort_run.protocol_version_id)
        if protocol is None or protocol.status != "reviewed_demo":
            raise ResearchError("Execução bloqueada: protocolo revisado ausente.")
        reviewed_outcome = self.db.scalar(
            select(func.count(OutcomeDefinitionModel.id)).where(
                OutcomeDefinitionModel.study_id == study.id,
                OutcomeDefinitionModel.institution_id == actor.institution_id,
                OutcomeDefinitionModel.review_status == "reviewed_demo",
            )
        )
        if not reviewed_outcome:
            raise ResearchError("Execução bloqueada: outcome revisado ausente.")
        critical = int(
            self.db.scalar(
                select(func.count(DataQualityFindingModel.id)).where(
                    DataQualityFindingModel.institution_id == actor.institution_id,
                    DataQualityFindingModel.status == "open",
                    DataQualityFindingModel.severity == "critical",
                )
            )
            or 0
        )
        if critical:
            raise ResearchError("Execução bloqueada por finding crítico de Data Quality.")
        results = self._select_results(cohort_run, plan.methods)
        provenance = {
            "aggregate_only": True,
            "ai_used_for_calculation": False,
            "analysis_engine": "prescripta-descriptive-analytics-v1",
            "analysis_plan_hash": plan.definition_hash,
            "cohort_run_hash": cohort_run.run_hash,
            "protocol_definition_hash": protocol.definition_hash,
            "data_snapshot_marker": cohort_run.data_snapshot_marker,
            "source_version_refs": sorted(
                set((cohort_run.source_version_refs or []) + (plan.source_refs or []))
            ),
        }
        basis = {
            "study_id": study.id,
            "plan_id": plan.id,
            "cohort_run_id": cohort_run.id,
            "results": results,
            "provenance": provenance,
        }
        analysis_run = ResearchAnalysisRunModel(
            study_id=study.id,
            analysis_plan_id=plan.id,
            cohort_run_id=cohort_run.id,
            institution_id=actor.institution_id,
            data_snapshot_marker=cohort_run.data_snapshot_marker,
            status="completed_demo",
            results=results,
            provenance=provenance,
            content_hash=canonical_sha256(basis),
            executed_by_user_id=actor.id,
            executed_at=datetime.now(UTC),
        )
        self.db.add(analysis_run)
        self.db.flush()
        self._audit(
            actor,
            "research.analysis.execute",
            "research_analysis_run",
            analysis_run.id,
            analysis_run.status,
            {"content_hash": analysis_run.content_hash, "aggregate_only": True},
        )
        return analysis_run

    def list_runs(self, study_id: str, actor: UserModel) -> list[ResearchAnalysisRunModel]:
        self._study(study_id, actor)
        return list(
            self.db.scalars(
                select(ResearchAnalysisRunModel)
                .where(
                    ResearchAnalysisRunModel.study_id == study_id,
                    ResearchAnalysisRunModel.institution_id == actor.institution_id,
                )
                .order_by(ResearchAnalysisRunModel.executed_at.desc())
            )
        )

    def export_package(self, analysis_run_id: str, actor: UserModel) -> ResearchPackageModel:
        run = self.db.get(ResearchAnalysisRunModel, analysis_run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Execução de análise não encontrada.")
        study = self._study(run.study_id, actor)
        plan = self._plan(run.analysis_plan_id, actor)
        cohort_run = self._cohort_run(run.cohort_run_id, actor)
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(
                ResearchSnapshotModel.cohort_run_id == cohort_run.id
            )
        )
        latest_dq = self.db.scalar(
            select(DataQualityRunModel)
            .where(DataQualityRunModel.institution_id == actor.institution_id)
            .order_by(DataQualityRunModel.executed_at.desc())
        )
        files = {
            "study.json": {
                "id": study.id,
                "title": study.title,
                "research_question": study.research_question,
                "objective": study.objective,
                "design": study.design,
                "synthetic_only": True,
            },
            "cohort.json": {
                "run_hash": cohort_run.run_hash,
                "result_count": cohort_run.result_count,
                "attrition": cohort_run.attrition,
                "snapshot_hash": snapshot.snapshot_hash if snapshot else None,
            },
            "analysis-plan.json": {
                "id": plan.id,
                "version": plan.version,
                "methods": plan.methods,
                "outputs": plan.planned_outputs,
                "definition_hash": plan.definition_hash,
            },
            "results.json": run.results,
            "data-quality.json": latest_dq.summary if latest_dq else {"status": "not_run"},
            "provenance.json": run.provenance,
            "README.txt": (
                "Pacote agregado e sintético. Não contém linhas de pacientes "
                "e não possui validade clínica."
            ),
        }
        file_hashes = {name: canonical_sha256(content) for name, content in files.items()}
        manifest = {
            "schema_version": "prescripta-research-package-v1",
            "analysis_run_id": run.id,
            "analysis_content_hash": run.content_hash,
            "aggregate_only": True,
            "synthetic_only": True,
            "files": file_hashes,
        }
        content_hash = canonical_sha256({"manifest": manifest, "files": files})
        existing = self.db.scalar(
            select(ResearchPackageModel).where(
                ResearchPackageModel.analysis_run_id == run.id,
                ResearchPackageModel.content_hash == content_hash,
            )
        )
        if existing:
            return existing
        package = ResearchPackageModel(
            study_id=study.id,
            analysis_run_id=run.id,
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
            "research.package.export",
            "research_package",
            package.id,
            "completed",
            {"content_hash": content_hash, "aggregate_only": True},
        )
        return package

    def patient_journey(self, study_id: str, patient_id: int, actor: UserModel) -> dict:
        study = self._study(study_id, actor)
        if not study.demo_only or study.data_source_classification != "synthetic":
            raise ResearchError("Patient Journey falhou fechado: estudo não sintético.")
        patient = self.db.get(PatientModel, patient_id)
        if patient is None or patient.institution_id != actor.institution_id:
            raise ResearchNotFound("Paciente sintético não encontrado.")
        events = list(
            self.db.scalars(
                select(PatientClinicalTimelineEventModel)
                .where(
                    PatientClinicalTimelineEventModel.patient_id == patient.id,
                    PatientClinicalTimelineEventModel.institution_id == actor.institution_id,
                )
                .order_by(
                    PatientClinicalTimelineEventModel.event_date,
                    PatientClinicalTimelineEventModel.id,
                )
            )
        )
        if not events or any(
            event.source_type != "synthetic_fixture"
            or not (event.provenance or {}).get("demo_only")
            for event in events
        ):
            raise ResearchError("Patient Journey falhou fechado: origem sintética não comprovada.")
        normalized = [
            {
                "event_ref": f"EVT-{event.id:05d}",
                "event_type": event.event_type,
                "occurred_at": json_compatible(event.event_date or event.created_at),
                "title": event.title,
                "summary": event.summary,
                "concept": {
                    "system": event.concept_system,
                    "code": event.concept_code,
                    "label": event.concept_label,
                },
                "source_type": event.source_type,
                "validation_status": event.validation_status,
            }
            for event in events
        ]
        patient_ref = (
            f"SYN-{canonical_sha256({'study_id': study.id, 'patient_id': patient.id})[:12]}"
        )
        self._audit(
            actor,
            "research.patient_journey.read",
            "research_study",
            study.id,
            "synthetic_only",
            {"event_count": len(normalized), "patient_ref": patient_ref},
        )
        return {
            "study_id": study.id,
            "patient_ref": patient_ref,
            "events": normalized,
            "event_count": len(normalized),
            "aggregate_only": False,
            "synthetic_only": True,
        }

    @staticmethod
    def _select_results(cohort_run: CohortRunModel, methods: list[str]) -> dict:
        analytics = cohort_run.analytics or {}
        results: dict = {"population_count": cohort_run.result_count, "aggregate_only": True}
        mapping = {
            "numeric_summary": "numeric",
            "categorical_distribution": "categorical",
            "prevalence": "prevalence",
            "baseline_table_1": "table_1",
            "resource_utilization": "utilization",
        }
        for method in methods:
            if method in mapping:
                results[mapping[method]] = analytics.get(mapping[method])
        results["missingness"] = analytics.get("missingness", {})
        results["attrition"] = cohort_run.attrition
        results["incidence"] = analytics.get(
            "incidence",
            {"status": "deferred", "reason": "person-time denominator is not validated"},
        )
        return results

    def _study(self, study_id: str, actor: UserModel) -> ResearchStudyModel:
        study = self.db.get(ResearchStudyModel, study_id)
        if study is None or study.institution_id != actor.institution_id:
            raise ResearchNotFound("Estudo não encontrado.")
        return study

    def _plan(self, plan_id: str, actor: UserModel) -> AnalysisPlanModel:
        plan = self.db.get(AnalysisPlanModel, plan_id)
        if plan is None or plan.institution_id != actor.institution_id:
            raise ResearchNotFound("Plano de análise não encontrado.")
        return plan

    def _cohort_run(self, run_id: str, actor: UserModel) -> CohortRunModel:
        run = self.db.get(CohortRunModel, run_id)
        if run is None or run.institution_id != actor.institution_id:
            raise ResearchNotFound("Execução de coorte não encontrada.")
        return run

    def _audit(
        self,
        actor: UserModel,
        action: str,
        resource_type: str,
        resource_id: str,
        status: str,
        details: dict,
    ) -> None:
        AuditService(self.db).record_action(
            user=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details,
        )
