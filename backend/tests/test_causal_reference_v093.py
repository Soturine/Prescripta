from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.schemas.research_v092_schema import (
    CausalAssumptions,
    ComparativeAnalysisRequest,
    IPTWConfig,
    PSMConfig,
    SyntheticResearchRecord,
)
from app.services.comparative_analytics_service import ComparativeAnalyticsEngine


def _reference_records() -> list[SyntheticResearchRecord]:
    records = []
    for index in range(12):
        records.extend(
            [
                SyntheticResearchRecord(
                    record_key=f"E{index}",
                    group="exposed",
                    outcome=index % 3 == 0,
                    event_day=5 if index % 3 == 0 else None,
                    follow_up_days=30,
                    covariates={"age": 42 + index * 1.7, "risk": 0.2 + index * 0.03},
                ),
                SyntheticResearchRecord(
                    record_key=f"C{index}",
                    group="comparator",
                    outcome=index % 5 == 0,
                    event_day=7 if index % 5 == 0 else None,
                    follow_up_days=30,
                    covariates={"age": 40 + index * 1.4, "risk": 0.15 + index * 0.025},
                ),
            ]
        )
    return records


def test_propensity_and_iptw_match_independent_golden() -> None:
    golden = json.loads((Path(__file__).parent / "fixtures/causal_reference_v093.json").read_text())
    records, _, treatment, propensity, _, _ = ComparativeAnalyticsEngine()._fit_propensity(
        _reference_records(), ["age", "risk"], golden["seed"]
    )
    assert len(records) == len(golden["propensity"])
    np.testing.assert_allclose(propensity, golden["propensity"], atol=golden["tolerance"])
    prevalence = float(np.mean(treatment))
    ate = np.where(
        treatment == 1,
        prevalence / propensity,
        (1 - prevalence) / (1 - propensity),
    )
    att = np.where(treatment == 1, 1.0, propensity / (1 - propensity))
    np.testing.assert_allclose(ate, golden["stabilized_ate_weights"], atol=0.002)
    np.testing.assert_allclose(att, golden["att_weights"], atol=0.002)
    assert abs(float(ate.sum() ** 2 / np.sum(ate**2)) - golden["stabilized_ate_ess"]) < 0.02
    assert abs(float(att.sum() ** 2 / np.sum(att**2)) - golden["att_ess"]) < 0.02


def test_full_production_psm_and_iptw_match_independent_end_to_end_reference() -> None:
    golden = json.loads((Path(__file__).parent / "fixtures/causal_reference_v093.json").read_text())
    records = _reference_records()
    propensity = np.asarray(golden["propensity"])
    treatment = np.asarray([record.group == "exposed" for record in records], dtype=int)
    outcomes = np.asarray([record.outcome for record in records], dtype=float)

    controls = {index for index, value in enumerate(treatment) if value == 0}
    treated = [index for index, value in enumerate(treatment) if value == 1]
    pairs: list[tuple[int, int]] = []
    for exposed in sorted(treated, key=lambda i: (propensity[i], records[i].record_key)):
        candidates = sorted(
            controls,
            key=lambda i: (abs(propensity[i] - propensity[exposed]), records[i].record_key),
        )
        selected = [
            item for item in candidates if abs(propensity[item] - propensity[exposed]) <= 0.3
        ]
        if selected:
            pairs.append((exposed, selected[0]))
            controls.remove(selected[0])
    independent_psm_rd = float(
        np.mean([outcomes[e] for e, _ in pairs]) - np.mean([outcomes[c] for _, c in pairs])
    )
    prevalence = float(np.mean(treatment))
    weights = np.where(
        treatment == 1,
        prevalence / propensity,
        (1 - prevalence) / (1 - propensity),
    )
    independent_iptw_rd = float(
        np.average(outcomes[treatment == 1], weights=weights[treatment == 1])
        - np.average(outcomes[treatment == 0], weights=weights[treatment == 0])
    )

    payload = ComparativeAnalysisRequest(
        exposed_cohort_run_id="e" * 36,
        comparator_cohort_run_id="c" * 36,
        data_quality_run_id="d" * 36,
        outcome_version_ids=["o" * 36],
        dataset_snapshot_marker="independent-reference-v010",
        dataset_snapshot_hash="a" * 64,
        covariates=["age", "risk"],
        records=records,
        small_cell_threshold=1,
        psm=PSMConfig(enabled=True, covariates=["age", "risk"], caliper=0.3, seed=17),
        iptw=IPTWConfig(enabled=True, covariates=["age", "risk"], seed=17),
        causal_assumptions=CausalAssumptions(
            consistency="acknowledged",
            exchangeability="needs_review",
            positivity="acknowledged",
            interference="not_applicable",
            residual_confounding="Residual confounding remains possible.",
            covariate_roles={"age": "confounder", "risk": "confounder"},
        ),
    )
    production = ComparativeAnalyticsEngine().calculate(payload)[0]["adjusted"]
    assert production["psm"]["matched_exposed_n"] == len(pairs)
    assert abs(production["psm"]["adjusted_risk_difference"] - independent_psm_rd) < 1e-7
    assert abs(production["iptw"]["adjusted_risk_difference"] - independent_iptw_rd) < 5e-4
    assert production["psm"]["status"] == production["iptw"]["status"] == "computed_experimental"
