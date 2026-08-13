"""Reproduce the independent v0.9.3 propensity/IPTW golden fixture.

This script deliberately does not import Prescripta's analytics engine. It uses
SciPy's optimizer plus explicit logistic and weight formulas as a second
implementation. It is optional and not installed as a runtime dependency.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import minimize


def main() -> None:
    rows = []
    for index in range(12):
        rows.extend(
            [
                [42 + index * 1.7, 0.2 + index * 0.03, 1],
                [40 + index * 1.4, 0.15 + index * 0.025, 0],
            ]
        )
    matrix = np.asarray([row[:2] for row in rows], dtype=float)
    treatment = np.asarray([row[2] for row in rows], dtype=float)
    standardized = (matrix - matrix.mean(axis=0)) / matrix.std(axis=0)

    def objective(beta: np.ndarray) -> float:
        linear = beta[0] + standardized @ beta[1:]
        loss = np.sum(np.logaddexp(0, linear) - treatment * linear)
        return float(loss + 0.5 * np.sum(beta[1:] ** 2))

    fit = minimize(objective, np.zeros(3), method="BFGS", tol=1e-12)
    linear = fit.x[0] + standardized @ fit.x[1:]
    propensity = 1 / (1 + np.exp(-linear))
    prevalence = float(np.mean(treatment))
    ate = np.where(
        treatment == 1,
        prevalence / propensity,
        (1 - prevalence) / (1 - propensity),
    )
    att = np.where(treatment == 1, 1.0, propensity / (1 - propensity))

    def ess(weights: np.ndarray) -> float:
        return float(np.sum(weights) ** 2 / np.sum(weights**2))

    payload = {
        "reference": "independent scipy.optimize manual penalized logistic and weights",
        "reference_version": f"scipy-{scipy.__version__}",
        "date": "2026-08-13",
        "methodology": "standardize; BFGS log-loss plus L2; explicit ATE/ATT formulas",
        "fixture": "numeric-no-ties-v1",
        "seed": 17,
        "tolerance": 0.0005,
        "propensity": [round(float(value), 9) for value in propensity],
        "stabilized_ate_weights": [round(float(value), 9) for value in ate],
        "att_weights": [round(float(value), 9) for value in att],
        "stabilized_ate_ess": round(ess(ate), 9),
        "att_ess": round(ess(att), 9),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["content_hash"] = hashlib.sha256(canonical.encode()).hexdigest()
    target = Path(__file__).parents[1] / "backend/tests/fixtures/causal_reference_v093.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
