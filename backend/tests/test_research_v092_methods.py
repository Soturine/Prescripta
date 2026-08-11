from __future__ import annotations

import math

import numpy as np
import pytest
from pydantic import ValidationError

from app.schemas.research_v092_schema import (
    CausalAssumptions,
    ComparativeAnalysisRequest,
    IPTWConfig,
    PSMConfig,
    ResearchQueryPreviewRequest,
    SyntheticResearchRecord,
)
from app.services.comparative_analytics_service import (
    ComparativeAnalyticsEngine,
    _binary_smd,
    _continuous_smd,
    _round,
    _weighted_smd,
)
from app.services.research_query_service import ResearchQueryPolicyError, ResearchQueryService


def _records(*, separated: bool = False) -> list[SyntheticResearchRecord]:
    records: list[SyntheticResearchRecord] = []
    for index in range(20):
        records.append(
            SyntheticResearchRecord(
                record_key=f"E-{index:02d}",
                group="exposed",
                outcome=index < 10,
                event_day=10 + index if index < 10 else None,
                follow_up_days=30 + index,
                covariates={
                    "age": 80 + index if separated else 40 + index,
                    "sex": "F" if index % 2 else "M",
                },
            )
        )
        records.append(
            SyntheticResearchRecord(
                record_key=f"C-{index:02d}",
                group="comparator",
                outcome=index < 5,
                event_day=12 + index if index < 5 else None,
                follow_up_days=32 + index,
                covariates={
                    "age": 20 + index if separated else 42 + index,
                    "sex": "F" if index % 2 else "M",
                },
            )
        )
    return records


def _payload(**overrides) -> ComparativeAnalysisRequest:
    values = {
        "exposed_cohort_run_id": "e" * 36,
        "comparator_cohort_run_id": "c" * 36,
        "data_quality_run_id": "d" * 36,
        "outcome_version_ids": ["o" * 36],
        "dataset_snapshot_marker": "synthetic-v092",
        "dataset_snapshot_hash": "a" * 64,
        "covariates": ["age", "sex"],
        "records": _records(),
        "small_cell_threshold": 5,
        "synthetic_only": True,
    }
    values.update(overrides)
    return ComparativeAnalysisRequest.model_validate(values)


def _assumptions() -> CausalAssumptions:
    return CausalAssumptions(
        consistency="acknowledged",
        exchangeability="needs_review",
        positivity="acknowledged",
        interference="not_applicable",
        residual_confounding="Residual and unmeasured confounding remain possible.",
        covariate_roles={"age": "confounder", "sex": "prognostic"},
    )


def test_comparative_measures_table_one_and_person_time_are_deterministic() -> None:
    engine = ComparativeAnalyticsEngine()
    first = engine.calculate(_payload())
    second = engine.calculate(_payload())
    assert first == second
    results, diagnostics, provenance = first
    measures = results["measures"]
    assert measures["event_counts"] == {"exposed": 10, "comparator": 5}
    assert measures["risk"]["exposed"] == 0.5
    assert measures["risk"]["comparator"] == 0.25
    assert measures["ratios"]["risk_ratio"]["estimate"] == 2.0
    assert measures["ratios"]["odds_ratio"]["estimate"] == 3.0
    assert measures["ratios"]["risk_ratio"]["ci_method"] == "log_wald_95"
    assert measures["incidence"]["status"] == "computed"
    assert diagnostics["table_1"]["exposed_n"] == 20
    assert any(row["variable"] == "age" for row in diagnostics["table_1"]["rows"])
    assert provenance["deterministic"] is True
    assert provenance["record_level_input_persisted"] is False


def test_small_cells_and_zero_cells_fail_closed_without_silent_correction() -> None:
    tiny = _records()[:8]
    tiny_payload = _payload(records=tiny, small_cell_threshold=5)
    results, _, _ = ComparativeAnalyticsEngine().calculate(tiny_payload)
    assert results["measures"] == {
        "status": "suppressed",
        "reason": "small_cell",
        "threshold": 5,
        "event_counts": {"exposed": None, "comparator": None},
        "derived_measures_withheld": True,
    }

    zero_events = [
        item.model_copy(update={"outcome": False, "event_day": None})
        for item in _records()
    ]
    results, _, _ = ComparativeAnalyticsEngine().calculate(
        _payload(records=zero_events, small_cell_threshold=1)
    )
    ratios = results["measures"]["ratios"]
    assert ratios["status"] == "not_computable"
    assert "explicit_continuity_correction" in ratios["reason"]
    assert results["measures"]["continuity_correction"] is None


def test_psm_and_iptw_are_deterministic_and_report_diagnostics() -> None:
    payload = _payload(
        psm=PSMConfig(enabled=True, covariates=["age", "sex"], caliper=0.3, seed=17),
        iptw=IPTWConfig(
            enabled=True,
            covariates=["age", "sex"],
            estimand="ATE",
            stabilized=True,
            truncation_percentiles=(1, 99),
            seed=17,
        ),
        causal_assumptions=_assumptions(),
    )
    first = ComparativeAnalyticsEngine().calculate(payload)[0]["adjusted"]
    second = ComparativeAnalyticsEngine().calculate(payload)[0]["adjusted"]
    assert first == second
    assert first["psm"]["status"] == "computed_experimental"
    assert first["psm"]["estimand"] == "ATT"
    assert first["psm"]["balance"]
    assert first["psm"]["matched_exposed_n"] > 0
    assert first["iptw"]["status"] == "computed_experimental"
    assert first["iptw"]["estimand"] == "ATE"
    assert first["iptw"]["effective_sample_size"] > 2
    assert first["iptw"]["truncation_percentiles"] == (1.0, 99.0)
    assert first["iptw"]["balance"]


def test_propensity_methods_abstain_on_no_overlap_and_reject_nan() -> None:
    payload = _payload(
        records=_records(separated=True),
        psm=PSMConfig(enabled=True, covariates=["age"], seed=2),
        iptw=IPTWConfig(enabled=True, covariates=["age"], seed=2),
        causal_assumptions=_assumptions(),
    )
    adjusted = ComparativeAnalyticsEngine().calculate(payload)[0]["adjusted"]
    assert adjusted["psm"]["status"] == "abstained"
    assert adjusted["iptw"]["status"] == "abstained"

    with pytest.raises(ValidationError, match="NaN/inf"):
        SyntheticResearchRecord(
            record_key="bad",
            group="exposed",
            outcome=False,
            follow_up_days=1,
            covariates={"age": math.nan},
        )


def _query(sql: str, **overrides) -> ResearchQueryPreviewRequest:
    values = {
        "study_id": "s" * 36,
        "dataset_snapshot_marker": "synthetic-v092",
        "natural_language_question": "Count approved aggregate comparison runs",
        "proposed_sql": sql,
        "purpose": "bounded synthetic aggregate query",
    }
    values.update(overrides)
    return ResearchQueryPreviewRequest.model_validate(values)


def test_query_ast_scopes_allowed_select_and_blocks_adversarial_sql() -> None:
    service = ResearchQueryService(None)  # type: ignore[arg-type]
    normalized, interpretation, cost = service._validate_and_scope(
        _query("SELECT count(id) AS total FROM research_aggregate_comparisons")
    )
    assert ":institution_id" in normalized
    assert ":study_id" in normalized
    assert "LIMIT 100" in normalized
    assert interpretation["read_only"] is True
    assert interpretation["tenant_scope_injected"] is True
    assert cost <= 10_000

    blocked = [
        "DELETE FROM research_aggregate_comparisons",
        (
            "SELECT id FROM research_aggregate_comparisons; "
            "SELECT id FROM research_aggregate_comparisons"
        ),
        "SELECT id FROM pg_catalog.pg_tables",
        "SELECT id FROM research_aggregate_comparisons UNION SELECT id FROM other_tenant",
        "SELECT pg_read_file('/etc/passwd') FROM research_aggregate_comparisons",
        "SELECT secret FROM research_aggregate_comparisons",
        "SELECT id FROM research_comparison_runs",
        "SELECT 1",
        "SHOW statement_timeout",
        (
            "SELECT a.id FROM research_aggregate_comparisons a "
            "JOIN research_aggregate_comparisons b ON a.id = b.id"
        ),
        "SELECT id FROM research_aggregate_comparisons WHERE (",
    ]
    for sql in blocked:
        with pytest.raises(ResearchQueryPolicyError):
            service._validate_and_scope(_query(sql))


def test_query_cost_budget_and_assumption_contract_fail_closed() -> None:
    service = ResearchQueryService(None)  # type: ignore[arg-type]
    with pytest.raises(ResearchQueryPolicyError, match="cost"):
        service._validate_and_scope(
            _query(
                "SELECT id, status, content_hash FROM research_aggregate_comparisons",
                cost_budget=1,
            )
        )
    with pytest.raises(ValidationError, match="assumptions"):
        _payload(psm=PSMConfig(enabled=True, covariates=["age"]))


def test_v092_schema_rejects_invalid_bounded_inputs() -> None:
    base = _records()[0].model_dump()
    with pytest.raises(ValidationError, match="30 covari"):
        SyntheticResearchRecord.model_validate(
            {**base, "covariates": {f"c{i}": i for i in range(31)}}
        )
    with pytest.raises(ValidationError, match="event_day"):
        SyntheticResearchRecord.model_validate({**base, "event_day": None})
    with pytest.raises(ValidationError, match="exceder"):
        SyntheticResearchRecord.model_validate(
            {**base, "follow_up_days": 5, "event_day": 6}
        )
    with pytest.raises(ValidationError, match="PSM exige"):
        PSMConfig(enabled=True)
    with pytest.raises(ValidationError, match="IPTW exige"):
        IPTWConfig(enabled=True)
    with pytest.raises(ValidationError, match="Percentis"):
        IPTWConfig(truncation_percentiles=(99, 1))
    with pytest.raises(ValidationError, match="grupos"):
        _payload(records=[item for item in _records() if item.group == "exposed"])
    duplicate = _records()
    duplicate[1] = duplicate[1].model_copy(update={"record_key": duplicate[0].record_key})
    with pytest.raises(ValidationError, match="único"):
        _payload(records=duplicate)
    with pytest.raises(ValidationError, match="não declarada"):
        _payload(
            psm=PSMConfig(enabled=True, covariates=["unknown"]),
            causal_assumptions=_assumptions(),
        )


def test_statistical_helpers_fail_closed_on_degenerate_inputs() -> None:
    assert _round(None) is None
    assert _round(math.inf) is None
    assert _continuous_smd([], [1.0]) is None
    assert _continuous_smd([1.0], [1.0]) == 0.0
    assert _continuous_smd([1.0], [2.0]) is None
    assert _binary_smd(0.0, 0.0) == 0.0
    assert _binary_smd(0.0, 1.0) is None
    assert _weighted_smd(
        np.asarray([1.0]), np.asarray([1]), np.asarray([1.0])
    ) is None
    assert _weighted_smd(
        np.asarray([1.0, 1.0]), np.asarray([1, 0]), np.asarray([1.0, 1.0])
    ) == 0.0
    assert _weighted_smd(
        np.asarray([1.0, 2.0]), np.asarray([1, 0]), np.asarray([1.0, 1.0])
    ) is None
    assert ComparativeAnalyticsEngine._numeric_summary([], 3) == {
        "n": 0,
        "mean": None,
        "sd": None,
        "missing": 3,
    }

    missing = [
        item.model_copy(update={"covariates": {"age": None}}) for item in _records()
    ]
    assert ComparativeAnalyticsEngine()._psm(
        missing, PSMConfig(enabled=True, covariates=["age"])
    )["status"] == "abstained"
    assert ComparativeAnalyticsEngine()._iptw(
        missing, IPTWConfig(enabled=True, covariates=["age"])
    )["status"] == "abstained"


@pytest.mark.parametrize("estimand,stabilized", [("ATT", True), ("ATT", False), ("ATE", False)])
def test_iptw_estimand_and_stabilization_branches(estimand: str, stabilized: bool) -> None:
    payload = _payload(
        iptw=IPTWConfig(
            enabled=True,
            covariates=["age", "sex"],
            estimand=estimand,
            stabilized=stabilized,
        ),
        causal_assumptions=_assumptions(),
    )
    result = ComparativeAnalyticsEngine().calculate(payload)[0]["adjusted"]["iptw"]
    assert result["status"] == "computed_experimental"
    assert result["estimand"] == estimand
    assert result["stabilized"] is stabilized
