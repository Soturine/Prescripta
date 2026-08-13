from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.schemas.research_v092_schema import SyntheticResearchRecord
from app.services.comparative_analytics_service import ComparativeAnalyticsEngine


def _reference_records() -> list[SyntheticResearchRecord]:
    records = []
    for index in range(12):
        records.extend(
            [
                SyntheticResearchRecord(
                    record_key=f"E{index}", group="exposed", outcome=index % 3 == 0,
                    event_day=5 if index % 3 == 0 else None, follow_up_days=30,
                    covariates={"age": 42 + index * 1.7, "risk": 0.2 + index * 0.03},
                ),
                SyntheticResearchRecord(
                    record_key=f"C{index}", group="comparator", outcome=index % 5 == 0,
                    event_day=7 if index % 5 == 0 else None, follow_up_days=30,
                    covariates={"age": 40 + index * 1.4, "risk": 0.15 + index * 0.025},
                ),
            ]
        )
    return records


def test_propensity_and_iptw_match_independent_golden() -> None:
    golden = json.loads(
        (Path(__file__).parent / "fixtures/causal_reference_v093.json").read_text()
    )
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
