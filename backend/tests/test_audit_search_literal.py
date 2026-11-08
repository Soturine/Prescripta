"""NEW-06: `%` e `_` digitados no filtro da auditoria são literais, não curingas SQL."""

from __future__ import annotations

from app.database.models import AuditEventModel
from app.repositories.audit_repository import AuditRepository


def _event(db, resource_id: str) -> None:
    db.add(
        AuditEventModel(
            action="synthetic.literal_search",
            resource_type="synthetic",
            resource_id=resource_id,
            status="ok",
            details={"note": resource_id},
        )
    )


def test_wildcard_characters_are_matched_literally(db_session) -> None:
    for resource_id in ("lote_01", "loteX01", "taxa 100%", "taxa 1000"):
        _event(db_session, resource_id)
    db_session.commit()
    repo = AuditRepository(db_session)

    def ids(**filters: str) -> set[str]:
        return {event.resource_id for event in repo.list_filtered(**filters)}

    assert ids(text="lote_01") == {"lote_01"}
    assert ids(text="100%") == {"taxa 100%"}
    assert ids(patient="lote_01") == {"lote_01"}
    assert ids(text="lote") == {"lote_01", "loteX01"}
