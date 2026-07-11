from __future__ import annotations

from typing import Any

from app.reports.schemas import ReportEvidenceBundle


def decision_timeline(bundle: ReportEvidenceBundle) -> list[dict[str, Any]]:
    if bundle.prescription_result is not None:
        audit_id = bundle.metadata.get("audit_id")
        checked_at = bundle.metadata.get("checked_at")
        ai_context = bundle.ai_context
        return [
            {
                "order": 1,
                "title": "Prescricao criada/avaliada",
                "status": "registrada",
                "at": checked_at,
                "details": {"audit_id": audit_id},
            },
            {
                "order": 2,
                "title": "Regras deterministicas executadas",
                "status": "concluido",
                "details": {"rules_fired": bundle.rules_fired},
            },
            {
                "order": 3,
                "title": "Alertas disparados",
                "status": f"{len(bundle.prescription_result.alerts)} alerta(s)",
                "details": {"risk_level": bundle.prescription_result.risk_level},
            },
            {
                "order": 4,
                "title": "Fontes consultadas",
                "status": "registrado" if bundle.sources else "sem fonte adicional",
                "details": {"sources": [source.source_id for source in bundle.sources]},
            },
            {
                "order": 5,
                "title": "Narrativa assistida",
                "status": (
                    "IA externa habilitada"
                    if ai_context.allow_external_ai
                    else "fallback local"
                ),
                "details": {
                    "provider": ai_context.provider,
                    "model": ai_context.model,
                    "send_identifiable_data": ai_context.send_identifiable_data,
                },
            },
            {
                "order": 6,
                "title": "Relatorio gerado",
                "status": "pendente de download/exportacao",
                "details": {"bundle_hash": bundle.hash()},
            },
        ]
    if bundle.protocol_run_result is not None:
        result = bundle.protocol_run_result
        return [
            {
                "order": 1,
                "title": "Protocolo selecionado",
                "status": result.get("protocol_title"),
                "details": {
                    "protocol_id": result.get("protocol_id"),
                    "protocol_version": result.get("protocol_version"),
                },
            },
            {
                "order": 2,
                "title": "Contexto do paciente avaliado",
                "status": "com paciente" if result.get("patient_id") else "sem paciente vinculado",
                "details": result.get("patient_context_summary") or {},
            },
            {
                "order": 3,
                "title": "Passos do protocolo revisados",
                "status": f"{len(result.get('selected_step_orders') or [])} passo(s) marcado(s)",
                "details": {"timeline": result.get("timeline") or []},
            },
            {
                "order": 4,
                "title": "Flags e calculos registrados",
                "status": f"{len(result.get('triage_flags') or [])} flag(s)",
                "details": {
                    "triage_flags": result.get("triage_flags") or [],
                    "calculated_values": result.get("calculated_values") or [],
                },
            },
            {
                "order": 5,
                "title": "Relatorio de protocolo gerado",
                "status": "registrado",
                "details": {"bundle_hash": bundle.hash()},
            },
        ]
    if bundle.reconciliation_result is not None:
        return [
            {
                "order": 1,
                "title": "Importacao clinica criada",
                "status": bundle.metadata.get("status"),
                "details": {"batch_id": bundle.metadata.get("batch_id")},
            },
            {
                "order": 2,
                "title": "Consentimento registrado",
                "status": "informado" if bundle.reconciliation_result.get("consent") else "ausente",
            },
            {
                "order": 3,
                "title": "Reconciliação granular criada",
                "status": "concluido",
                "details": bundle.reconciliation_result.get("summary", {}),
            },
            {
                "order": 4,
                "title": "Relatorio de reconciliacao gerado",
                "status": "registrado",
                "details": {"bundle_hash": bundle.hash()},
            },
        ]
    if bundle.audit_result is not None:
        return [
            {
                "order": 1,
                "title": "Filtros aplicados",
                "status": "concluido",
                "details": bundle.audit_result.get("filters", {}),
            },
            {
                "order": 2,
                "title": "Eventos agregados",
                "status": f"{bundle.audit_result.get('total_events', 0)} evento(s)",
            },
            {
                "order": 3,
                "title": "Relatorio de auditoria gerado",
                "status": "registrado",
                "details": {"bundle_hash": bundle.hash()},
            },
        ]
    return []


def evidence_view(bundle: ReportEvidenceBundle) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    if bundle.prescription_result is not None:
        for alert in bundle.prescription_result.alerts:
            source = _source(bundle, alert.source_id)
            evidence.append(
                {
                    "code": alert.code,
                    "severity": alert.severity,
                    "rule_id": alert.rule_id,
                    "source_id": alert.source_id,
                    "source_name": source.source_name if source else "fonte interna",
                    "jurisdiction": source.jurisdiction if source else "BR",
                    "validation_status": source.validation_status if source else "internal",
                    "evidence_summary": alert.evidence_summary,
                    "evidence_type": source.evidence_type if source else "audit_record",
                    "confidence": source.confidence if source else "internal",
                    "review_status": source.validation_status if source else "internal",
                }
            )
    for source in bundle.sources:
        if not any(item.get("source_id") == source.source_id for item in evidence):
            evidence.append(
                {
                    "source_id": source.source_id,
                    "source_name": source.source_name,
                    "jurisdiction": source.jurisdiction,
                    "validation_status": source.validation_status,
                    "evidence_type": source.evidence_type,
                    "confidence": source.confidence or "nao informado",
                    "review_status": source.validation_status,
                }
            )
    return evidence


def _source(bundle: ReportEvidenceBundle, source_id: str):
    for source in bundle.sources:
        if source.source_id == source_id:
            return source
    return None
