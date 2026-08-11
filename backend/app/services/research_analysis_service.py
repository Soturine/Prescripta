from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import (
    AnalysisPlanModel,
    AnalysisPlanOutcomeModel,
    AnalysisRunOutcomeModel,
    CohortDefinitionVersionModel,
    CohortRunModel,
    DataQualityFindingModel,
    DataQualityRunModel,
    EvidenceSourceModel,
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
        outcome_version_ids = definition.pop("outcome_version_ids")
        requested_dq_id = definition.pop("data_quality_run_id")
        outcomes = self._resolve_outcomes(study.id, outcome_version_ids, actor)
        dq_run = self._resolve_data_quality_run(
            cohort_run, actor, requested_dq_id=requested_dq_id
        )
        definition_basis = {
            **definition,
            "outcome_version_refs": [self._outcome_ref(item) for item in outcomes],
            "data_quality_run_ref": self._dq_ref(dq_run),
        }
        plan = AnalysisPlanModel(
            study_id=study.id,
            institution_id=actor.institution_id,
            data_quality_run_id=dq_run.id,
            version=version,
            **json_compatible(definition),
            definition_hash=canonical_sha256(definition_basis),
            status="draft",
            authored_by_user_id=actor.id,
        )
        self.db.add(plan)
        self.db.flush()
        for outcome in outcomes:
            self.db.add(
                AnalysisPlanOutcomeModel(
                    analysis_plan_id=plan.id,
                    outcome_version_id=outcome.id,
                    **self._outcome_ref(outcome, relational=True),
                )
            )
        self.db.flush()
        plan.outcome_version_refs = [self._outcome_ref(item) for item in outcomes]
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
        bindings = self._plan_outcomes(plan.id)
        if not bindings:
            raise ResearchError("Plano sem versões exatas de outcome.")
        for binding in bindings:
            outcome = self.db.get(OutcomeDefinitionModel, binding.outcome_version_id)
            if (
                outcome is None
                or outcome.institution_id != actor.institution_id
                or outcome.study_id != plan.study_id
                or outcome.review_status != "reviewed_demo"
                or outcome.definition_hash != binding.outcome_hash
            ):
                raise ResearchError("Outcome vinculado está ausente, alterado ou sem revisão.")
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
        outcome_bindings = self._plan_outcomes(plan.id)
        if not outcome_bindings:
            raise ResearchError("Execução bloqueada: versões exatas de outcome ausentes.")
        outcomes: list[OutcomeDefinitionModel] = []
        for binding in outcome_bindings:
            outcome = self.db.get(OutcomeDefinitionModel, binding.outcome_version_id)
            if (
                outcome is None
                or outcome.study_id != study.id
                or outcome.institution_id != actor.institution_id
                or outcome.review_status != "reviewed_demo"
                or outcome.definition_hash != binding.outcome_hash
            ):
                raise ResearchError("Execução bloqueada: outcome exato inválido ou alterado.")
            outcomes.append(outcome)
        dq_run = self._resolve_data_quality_run(
            cohort_run, actor, requested_dq_id=plan.data_quality_run_id
        )
        critical = int(
            self.db.scalar(
                select(func.count(DataQualityFindingModel.id)).where(
                    DataQualityFindingModel.run_id == dq_run.id,
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
            "data_quality_run": self._dq_ref(dq_run),
            "outcome_versions": [self._outcome_ref(item) for item in outcomes],
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
            data_quality_run_id=dq_run.id,
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
        for outcome in outcomes:
            self.db.add(
                AnalysisRunOutcomeModel(
                    analysis_run_id=analysis_run.id,
                    outcome_version_id=outcome.id,
                    **self._outcome_ref(outcome, relational=True),
                )
            )
        self.db.flush()
        analysis_run.outcome_version_refs = [self._outcome_ref(item) for item in outcomes]
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
        protocol = self.db.get(StudyProtocolVersionModel, cohort_run.protocol_version_id)
        cohort_version = self.db.get(CohortDefinitionVersionModel, cohort_run.cohort_version_id)
        if protocol is None or cohort_version is None:
            raise ResearchError("Lineage de protocolo/coorte está incompleto.")
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(
                ResearchSnapshotModel.cohort_run_id == cohort_run.id
            )
        )
        dq_run = (
            self.db.get(DataQualityRunModel, run.data_quality_run_id)
            if run.data_quality_run_id
            else None
        )
        outcome_bindings = list(
            self.db.scalars(
                select(AnalysisRunOutcomeModel)
                .where(AnalysisRunOutcomeModel.analysis_run_id == run.id)
                .order_by(AnalysisRunOutcomeModel.outcome_version_id)
            )
        )
        outcomes = [
            self.db.get(OutcomeDefinitionModel, binding.outcome_version_id)
            for binding in outcome_bindings
        ]
        if any(item is None for item in outcomes):
            raise ResearchError("Lineage de outcome do run está quebrado.")
        source_refs = sorted(
            set(protocol.source_refs or [])
            | set(cohort_run.source_version_refs or [])
            | set(plan.source_refs or [])
            | {ref for item in outcomes if item for ref in (item.source_refs or [])}
        )
        evidence_sources = list(
            self.db.scalars(
                select(EvidenceSourceModel).where(
                    EvidenceSourceModel.institution_id == actor.institution_id,
                    EvidenceSourceModel.identifier.in_(source_refs),
                )
            )
        ) if source_refs else []
        files = {
            "study.json": {
                "id": study.id,
                "title": study.title,
                "research_question": study.research_question,
                "objective": study.objective,
                "design": study.design,
                "synthetic_only": True,
            },
            "protocol.json": {
                "id": protocol.id,
                "version": protocol.version,
                "definition_hash": protocol.definition_hash,
                "status": protocol.status,
                "source_refs": sorted(protocol.source_refs or []),
            },
            "cohort.json": {
                "definition_version_id": cohort_version.id,
                "definition_hash": cohort_version.definition_hash,
                "cohort_run_id": cohort_run.id,
                "run_hash": cohort_run.run_hash,
                "result_count": cohort_run.result_count,
                "attrition": cohort_run.attrition,
                "snapshot_hash": snapshot.snapshot_hash if snapshot else None,
            },
            "concept-set-refs.json": {
                "concept_set_version_ids": sorted(
                    {
                        ref
                        for item in outcomes
                        if item
                        for ref in (item.concept_set_version_ids or [])
                    }
                )
            },
            "outcomes.json": {
                "versions": [
                    {
                        **self._outcome_ref(item),
                        "domain": item.domain,
                        "concept_set_version_ids": sorted(item.concept_set_version_ids or []),
                        "event_qualification": item.event_qualification,
                        "observation_window": item.observation_window,
                        "temporal_relationship": item.temporal_relationship,
                        "source_refs": sorted(item.source_refs or []),
                        "limitations": sorted(item.limitations or []),
                    }
                    for item in outcomes
                    if item
                ]
            },
            "analysis-plan.json": {
                "id": plan.id,
                "version": plan.version,
                "methods": plan.methods,
                "outputs": plan.planned_outputs,
                "definition_hash": plan.definition_hash,
                "outcome_versions": [
                    self._binding_ref(item) for item in outcome_bindings
                ],
            },
            "results.json": run.results,
            "data-quality-summary.json": (
                {**self._dq_ref(dq_run), "summary": dq_run.summary}
                if dq_run
                else {
                    "status": "legacy_unscoped",
                    "reason": "Run histórico sem vínculo de Data Quality; nenhum run foi inferido.",
                }
            ),
            "provenance.json": run.provenance,
            "sources.json": {
                "source_refs": source_refs,
                "evidence_sources": [
                    {
                        "id": item.id,
                        "identifier": item.identifier,
                        "title": item.title,
                        "source_type": item.source_type,
                        "source_version": item.source_version,
                        "content_hash": item.content_hash,
                        "review_status": item.review_status,
                    }
                    for item in sorted(evidence_sources, key=lambda value: value.identifier)
                ],
            },
            "limitations.json": {
                "synthetic_only": True,
                "aggregate_only": True,
                "limitations": sorted(
                    set(protocol.limitations or [])
                    | set(plan.limitations or [])
                    | {value for item in outcomes if item for value in (item.limitations or [])}
                ),
                "claims_not_supported": [
                    "clinical_validity",
                    "causal_validity",
                    "regulatory_validity",
                    "ohdsi_network_readiness",
                ],
            },
            "terminology.json": {
                "status": "not_used",
                "reason": "Este run histórico não vinculou releases governadas de terminology.",
                "release_refs": [],
            },
            "mapping-refs.json": {
                "status": "not_used",
                "reason": "Nenhum mapping governado participou deste run.",
                "mapping_hashes": [],
            },
            "omop-etl-lineage.json": {
                "status": "not_applicable",
                "reason": "A análise não utilizou o adapter OMOP.",
            },
            "compatibility.json": {
                "level": "prescripta_internal",
                "omop_used": False,
                "ohdsi_tool_validated": False,
            },
        }
        file_hashes = {name: canonical_sha256(content) for name, content in files.items()}
        manifest = {
            "schema_version": "prescripta-research-package-v2",
            "prescripta_version": "0.9.1",
            "analysis_run_id": run.id,
            "analysis_content_hash": run.content_hash,
            "aggregate_only": True,
            "synthetic_only": True,
            "study_id": study.id,
            "protocol_version": {"id": protocol.id, "hash": protocol.definition_hash},
            "cohort": {
                "definition_version_id": cohort_version.id,
                "definition_hash": cohort_version.definition_hash,
                "run_id": cohort_run.id,
                "run_hash": cohort_run.run_hash,
                "snapshot_hash": snapshot.snapshot_hash if snapshot else None,
            },
            "outcome_versions": [self._binding_ref(item) for item in outcome_bindings],
            "analysis_plan": {
                "id": plan.id,
                "version": plan.version,
                "hash": plan.definition_hash,
            },
            "data_quality_run": self._dq_ref(dq_run) if dq_run else None,
            "terminology_release_refs": [],
            "mapping_hashes": [],
            "adapter_versions": {"research": "prescripta-descriptive-analytics-v1"},
            "limitations_summary": files["limitations.json"]["claims_not_supported"],
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

    def verify_package(self, package_id: str, actor: UserModel) -> dict:
        package = self.db.get(ResearchPackageModel, package_id)
        if package is None or package.institution_id != actor.institution_id:
            raise ResearchNotFound("Research Package não encontrado.")
        manifest = package.manifest or {}
        if manifest.get("schema_version") not in {
            "prescripta-research-package-v1",
            "prescripta-research-package-v2",
        }:
            return {"valid": False, "errors": ["unknown_schema"]}
        expected = manifest.get("files", {})
        actual = {name: canonical_sha256(content) for name, content in package.files.items()}
        errors: list[str] = []
        for name in expected:
            if name not in actual:
                errors.append(f"missing_file:{name}")
            elif expected[name] != actual[name]:
                errors.append(f"hash_mismatch:{name}")
        for name in actual:
            if name not in expected:
                errors.append(f"unlisted_file:{name}")
        calculated_package_hash = canonical_sha256(
            {"manifest": manifest, "files": package.files}
        )
        if calculated_package_hash != package.content_hash:
            errors.append("package_hash_mismatch")
        if manifest.get("analysis_run_id") != package.analysis_run_id:
            errors.append("analysis_lineage_mismatch")
        result = {
            "valid": not errors,
            "schema_version": manifest.get("schema_version"),
            "package_id": package.id,
            "content_hash": package.content_hash,
            "errors": sorted(errors),
        }
        self._audit(
            actor,
            "research.package.verify",
            "research_package",
            package.id,
            "valid" if not errors else "invalid",
            {"error_count": len(errors), "content_hash": package.content_hash},
        )
        return result

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

    def _resolve_outcomes(
        self,
        study_id: str,
        requested_ids: list[str],
        actor: UserModel,
    ) -> list[OutcomeDefinitionModel]:
        if requested_ids:
            outcomes = [self.db.get(OutcomeDefinitionModel, item) for item in requested_ids]
        else:
            candidates = list(
                self.db.scalars(
                    select(OutcomeDefinitionModel)
                    .where(
                        OutcomeDefinitionModel.study_id == study_id,
                        OutcomeDefinitionModel.institution_id == actor.institution_id,
                        OutcomeDefinitionModel.review_status == "reviewed_demo",
                    )
                    .order_by(
                        OutcomeDefinitionModel.name,
                        OutcomeDefinitionModel.version.desc(),
                    )
                )
            )
            latest_by_name: dict[str, OutcomeDefinitionModel] = {}
            for item in candidates:
                latest_by_name.setdefault(item.name, item)
            outcomes = list(latest_by_name.values())
        if not outcomes:
            raise ResearchError("O plano exige ao menos uma versão exata de outcome revisada.")
        if any(
            item is None
            or item.study_id != study_id
            or item.institution_id != actor.institution_id
            or item.review_status != "reviewed_demo"
            or item.reviewed_by_user_id is None
            for item in outcomes
        ):
            raise ResearchError("Outcome inexistente, cross-tenant ou sem revisão humana.")
        return sorted(outcomes, key=lambda item: item.id)  # type: ignore[union-attr]

    def _resolve_data_quality_run(
        self,
        cohort_run: CohortRunModel,
        actor: UserModel,
        *,
        requested_dq_id: str | None,
    ) -> DataQualityRunModel:
        snapshot = self.db.scalar(
            select(ResearchSnapshotModel).where(
                ResearchSnapshotModel.cohort_run_id == cohort_run.id
            )
        )
        if snapshot is None:
            raise ResearchError("Snapshot exato da coorte não foi encontrado.")
        if requested_dq_id:
            candidates = [self.db.get(DataQualityRunModel, requested_dq_id)]
        else:
            candidates = list(
                self.db.scalars(
                    select(DataQualityRunModel).where(
                        DataQualityRunModel.institution_id == actor.institution_id,
                        DataQualityRunModel.study_id == cohort_run.study_id,
                        DataQualityRunModel.cohort_run_id == cohort_run.id,
                        DataQualityRunModel.data_snapshot_marker
                        == cohort_run.data_snapshot_marker,
                        DataQualityRunModel.data_snapshot_hash == snapshot.snapshot_hash,
                        DataQualityRunModel.scope_status == "scoped",
                        DataQualityRunModel.status == "completed",
                    )
                )
            )
        if len(candidates) != 1:
            raise ResearchError(
                "Informe o Data Quality run exato; não existe um único run "
                "compatível com o snapshot."
            )
        dq_run = candidates[0]
        if (
            dq_run is None
            or dq_run.institution_id != actor.institution_id
            or dq_run.study_id != cohort_run.study_id
            or dq_run.cohort_run_id != cohort_run.id
            or dq_run.data_snapshot_marker != cohort_run.data_snapshot_marker
            or dq_run.data_snapshot_hash != snapshot.snapshot_hash
            or dq_run.scope_status != "scoped"
            or dq_run.status != "completed"
        ):
            raise ResearchError("Data Quality run incompatível com study/coorte/snapshot.")
        return dq_run

    def _plan_outcomes(self, plan_id: str) -> list[AnalysisPlanOutcomeModel]:
        return list(
            self.db.scalars(
                select(AnalysisPlanOutcomeModel)
                .where(AnalysisPlanOutcomeModel.analysis_plan_id == plan_id)
                .order_by(AnalysisPlanOutcomeModel.outcome_version_id)
            )
        )

    @staticmethod
    def _outcome_ref(
        outcome: OutcomeDefinitionModel,
        *,
        relational: bool = False,
    ) -> dict:
        terminology_refs = sorted(outcome.concept_set_version_ids or [])
        if relational:
            return {
                "outcome_logical_name": outcome.name,
                "outcome_version": outcome.version,
                "outcome_hash": outcome.definition_hash,
                "review_status": outcome.review_status,
                "reviewed_by_user_id": outcome.reviewed_by_user_id,
                "terminology_refs": terminology_refs,
            }
        return {
            "outcome_id": outcome.name,
            "outcome_version_id": outcome.id,
            "version": outcome.version,
            "content_hash": outcome.definition_hash,
            "review_status": outcome.review_status,
            "reviewed_by_user_id": outcome.reviewed_by_user_id,
            "terminology_refs": terminology_refs,
        }

    @staticmethod
    def _binding_ref(binding: AnalysisPlanOutcomeModel | AnalysisRunOutcomeModel) -> dict:
        return {
            "outcome_id": binding.outcome_logical_name,
            "outcome_version_id": binding.outcome_version_id,
            "version": binding.outcome_version,
            "content_hash": binding.outcome_hash,
            "review_status": binding.review_status,
            "reviewed_by_user_id": binding.reviewed_by_user_id,
            "terminology_refs": sorted(binding.terminology_refs or []),
        }

    @staticmethod
    def _dq_ref(run: DataQualityRunModel) -> dict:
        return {
            "id": run.id,
            "study_id": run.study_id,
            "cohort_run_id": run.cohort_run_id,
            "data_snapshot_marker": run.data_snapshot_marker,
            "data_snapshot_hash": run.data_snapshot_hash,
            "ruleset_version": run.ruleset_version,
            "terminology_snapshot": run.terminology_snapshot,
            "content_hash": run.content_hash,
            "scope_status": run.scope_status,
        }

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
