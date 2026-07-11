from __future__ import annotations

import html
from typing import Any

from app.reports.schemas import ReportEvidenceBundle, ReportNarrativeComposition
from app.reports.templates import LEGAL_NOTICE


def render_report_html(
    *,
    title: str,
    bundle: ReportEvidenceBundle,
    narrative: ReportNarrativeComposition,
    timeline: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> str:
    sections = [
        _section(
            "Resumo",
            [
                ("Tipo", title),
                ("Hash do EvidenceBundle", bundle.hash()),
                ("Template", bundle.report_version),
                ("Provider IA", narrative.provider),
                ("Modelo IA", narrative.model or "deterministico"),
                ("Fallback", "sim" if narrative.fallback_used else "nao"),
            ],
        ),
        _paragraph_section("Resumo executivo", narrative.narrative.executive_summary),
        _paragraph_section("Explicacao profissional", narrative.narrative.professional_explanation),
        _prescription_section(bundle),
        _protocol_section(bundle),
        _reconciliation_section(bundle),
        _audit_section(bundle),
        _table_section("Evidencias da decisao", evidence),
        _timeline_section(timeline),
        _paragraph_section("Limitacoes", narrative.narrative.limitations_note),
        _paragraph_section("Aviso legal", LEGAL_NOTICE),
    ]
    body = "\n".join(section for section in sections if section)
    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #162033; margin: 32px; }}
    h1 {{ font-size: 24px; margin: 0 0 4px; }}
    h2 {{ font-size: 16px; margin: 24px 0 8px; border-bottom: 1px solid #d7dde8;
      padding-bottom: 4px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
    th, td {{ border: 1px solid #d7dde8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f4f7fb; }}
    .meta {{ color: #526070; font-size: 12px; }}
    .notice {{ background: #fff7ed; border: 1px solid #fed7aa; padding: 10px; }}
  </style>
</head>
<body>
  <h1>Prescripta</h1>
  <p class="meta">{html.escape(title)}</p>
  {body}
</body>
</html>
""".strip()


def render_report_lines(
    *,
    title: str,
    bundle: ReportEvidenceBundle,
    narrative: ReportNarrativeComposition,
    timeline: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> list[str]:
    lines = [
        "Prescripta",
        title,
        f"EvidenceBundle hash: {bundle.hash()}",
        f"Template: {bundle.report_version}",
        f"Provider IA: {narrative.provider}",
        f"Modelo IA: {narrative.model or 'deterministico'}",
        f"Fallback: {'sim' if narrative.fallback_used else 'nao'}",
        "",
        "Resumo executivo",
        narrative.narrative.executive_summary or "-",
        "",
        "Explicacao profissional",
        narrative.narrative.professional_explanation or "-",
    ]
    if bundle.prescription_result is not None:
        prescription = bundle.prescription_result
        lines.extend(
            [
                "",
                "Prescricao",
                f"Medicamento: {prescription.medication_name}",
                f"Principio ativo: {prescription.active_ingredient or '-'}",
                f"Dose: {prescription.dose_per_administration}",
                f"Frequencia: {prescription.frequency}",
                f"Dose diaria: {prescription.daily_dose}",
                f"Dose acumulada: {prescription.accumulated_dose or '-'}",
                f"Status: {prescription.status}",
                f"Risco: {prescription.risk_level}",
            ]
        )
    if bundle.protocol_run_result is not None:
        protocol = bundle.protocol_run_result
        lines.extend(
            [
                "",
                "Protocolo",
                f"Nome: {protocol.get('protocol_title') or '-'}",
                f"Versao: {protocol.get('protocol_version') or '-'}",
                f"Categoria: {protocol.get('protocol_category') or '-'}",
                f"Severidade: {protocol.get('protocol_severity') or '-'}",
                f"Paciente: {protocol.get('patient_reference') or '-'}",
                f"Flags: {'; '.join(protocol.get('triage_flags') or []) or '-'}",
            ]
        )
    if bundle.reconciliation_result is not None:
        lines.extend(
            ["", "Reconciliacao", _short_json(bundle.reconciliation_result.get("summary"))]
        )
    if bundle.audit_result is not None:
        lines.extend(["", "Auditoria", f"Eventos: {bundle.audit_result.get('total_events', 0)}"])
    lines.extend(["", "Evidencias"])
    for item in evidence:
        lines.append(
            f"- {item.get('code') or item.get('source_id')}: "
            f"{item.get('evidence_summary') or item.get('source_name') or '-'}"
        )
    lines.extend(["", "Linha do tempo"])
    for item in timeline:
        lines.append(f"- {item.get('title')}: {item.get('status')}")
    lines.extend(["", "Limitacoes", narrative.narrative.limitations_note or "-", "", LEGAL_NOTICE])
    return lines


def _section(title: str, rows: list[tuple[str, str]]) -> str:
    body = "".join(
        f"<tr><th>{html.escape(label)}</th><td>{html.escape(value)}</td></tr>"
        for label, value in rows
    )
    return f"<h2>{html.escape(title)}</h2><table>{body}</table>"


def _paragraph_section(title: str, value: str) -> str:
    if not value:
        return ""
    return f"<h2>{html.escape(title)}</h2><p>{html.escape(value)}</p>"


def _prescription_section(bundle: ReportEvidenceBundle) -> str:
    prescription = bundle.prescription_result
    if prescription is None:
        return ""
    rows = [
        ("Paciente", bundle.patient_context.patient_reference if bundle.patient_context else "-"),
        ("Medicamento", prescription.medication_name),
        ("Principio ativo", prescription.active_ingredient or "-"),
        ("Dose", prescription.dose_per_administration),
        ("Frequencia", prescription.frequency),
        ("Dose diaria", prescription.daily_dose),
        ("Dose acumulada", prescription.accumulated_dose or "-"),
        ("Duracao", prescription.duration or "-"),
        ("Status", prescription.status),
        ("Risco", prescription.risk_level),
    ]
    return _section("Prescricao", rows)


def _protocol_section(bundle: ReportEvidenceBundle) -> str:
    result = bundle.protocol_run_result
    if result is None:
        return ""
    rows = [
        ("Protocolo", str(result.get("protocol_title") or "-")),
        ("Versao", str(result.get("protocol_version") or "-")),
        ("Categoria", str(result.get("protocol_category") or "-")),
        ("Severidade", str(result.get("protocol_severity") or "-")),
        ("Paciente", str(result.get("patient_reference") or "-")),
        ("Flags", "; ".join(result.get("triage_flags") or []) or "-"),
        ("Calculculos", _short_json(result.get("calculated_values") or [])),
    ]
    return _section("Protocolo rapido", rows)


def _reconciliation_section(bundle: ReportEvidenceBundle) -> str:
    if bundle.reconciliation_result is None:
        return ""
    summary = bundle.reconciliation_result.get("summary", {})
    rows = [(str(key), str(value)) for key, value in summary.items()]
    return _section("Reconciliacao clinica", rows)


def _audit_section(bundle: ReportEvidenceBundle) -> str:
    if bundle.audit_result is None:
        return ""
    rows = [
        ("Eventos", str(bundle.audit_result.get("total_events", 0))),
        ("Filtros", _short_json(bundle.audit_result.get("filters", {}))),
    ]
    return _section("Auditoria", rows)


def _table_section(title: str, rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    headers = sorted({key for row in rows for key in row})
    head = "".join(f"<th>{html.escape(header)}</th>" for header in headers)
    body = ""
    for row in rows:
        body += (
            "<tr>"
            + "".join(f"<td>{html.escape(str(row.get(header, '')))}</td>" for header in headers)
            + "</tr>"
        )
    return (
        f"<h2>{html.escape(title)}</h2><table><thead><tr>{head}</tr></thead>"
        f"<tbody>{body}</tbody></table>"
    )


def _timeline_section(timeline: list[dict[str, Any]]) -> str:
    if not timeline:
        return ""
    items = "".join(
        f"<li><strong>{html.escape(str(item.get('title', '')))}</strong>: "
        f"{html.escape(str(item.get('status', '')))}</li>"
        for item in timeline
    )
    return f"<h2>Linha do tempo da decisao</h2><ol>{items}</ol>"


def _short_json(value: Any) -> str:
    if value is None:
        return "-"
    return str(value)[:500]
