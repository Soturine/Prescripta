from __future__ import annotations

import math
from statistics import fmean, stdev
from typing import Any

import numpy as np
import sklearn
from sklearn.feature_extraction import DictVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.schemas.research_v092_schema import (
    ComparativeAnalysisRequest,
    IPTWConfig,
    PSMConfig,
    SyntheticResearchRecord,
)

STATS_ENGINE_VERSION = "prescripta-comparative-v1"
METHOD_LIBRARY = f"scikit-learn-{sklearn.__version__}"


class ComparativeAnalyticsError(ValueError):
    pass


def _round(value: float | None, digits: int = 8) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def _sample_sd(values: list[float]) -> float:
    return stdev(values) if len(values) > 1 else 0.0


def _continuous_smd(a: list[float], b: list[float]) -> float | None:
    if not a or not b:
        return None
    pooled = math.sqrt((_sample_sd(a) ** 2 + _sample_sd(b) ** 2) / 2)
    if pooled == 0:
        return 0.0 if fmean(a) == fmean(b) else None
    return (fmean(a) - fmean(b)) / pooled


def _binary_smd(pa: float, pb: float) -> float | None:
    denominator = math.sqrt((pa * (1 - pa) + pb * (1 - pb)) / 2)
    if denominator == 0:
        return 0.0 if pa == pb else None
    return (pa - pb) / denominator


def _weighted_mean(values: np.ndarray, weights: np.ndarray) -> float:
    return float(np.sum(values * weights) / np.sum(weights))


def _weighted_smd(
    values: np.ndarray,
    treatment: np.ndarray,
    weights: np.ndarray,
) -> float | None:
    exposed = treatment == 1
    comparator = ~exposed
    if not np.any(exposed) or not np.any(comparator):
        return None
    ea = values[exposed]
    eb = values[comparator]
    wa = weights[exposed]
    wb = weights[comparator]
    ma = _weighted_mean(ea, wa)
    mb = _weighted_mean(eb, wb)
    va = _weighted_mean((ea - ma) ** 2, wa)
    vb = _weighted_mean((eb - mb) ** 2, wb)
    denominator = math.sqrt((va + vb) / 2)
    if denominator == 0:
        return 0.0 if ma == mb else None
    return (ma - mb) / denominator


class ComparativeAnalyticsEngine:
    """Deterministic synthetic/demo analytics. It never calls an LLM."""

    def calculate(self, payload: ComparativeAnalysisRequest) -> tuple[dict, dict, dict]:
        exposed = [item for item in payload.records if item.group == "exposed"]
        comparator = [item for item in payload.records if item.group == "comparator"]
        table_one = self._table_one(exposed, comparator, payload.covariates)
        measures = self._measures(
            exposed,
            comparator,
            payload.denominator_unit,
            payload.continuity_correction,
            payload.small_cell_threshold,
        )
        diagnostics: dict[str, Any] = {
            "table_1": table_one,
            "warnings": [],
            "scientific_notice": (
                "Exploratory research signal — not a causal conclusion. Synthetic/demo only."
            ),
        }
        adjusted: dict[str, Any] = {}
        if payload.psm.enabled:
            adjusted["psm"] = self._psm(payload.records, payload.psm)
            diagnostics["warnings"].extend(adjusted["psm"].get("warnings", []))
        if payload.iptw.enabled:
            adjusted["iptw"] = self._iptw(payload.records, payload.iptw)
            diagnostics["warnings"].extend(adjusted["iptw"].get("warnings", []))
        if payload.sensitivity.enabled:
            adjusted["sensitivity"] = self._sensitivity(payload)
        results = {
            "table_1": table_one,
            "measures": measures,
            "adjusted": adjusted,
            "label": (
                "experimental adjusted research estimate"
                if adjusted
                else "descriptive estimate"
            ),
        }
        provenance = {
            "stats_engine_version": STATS_ENGINE_VERSION,
            "method_library": METHOD_LIBRARY,
            "deterministic": True,
            "seed": {"psm": payload.psm.seed, "iptw": payload.iptw.seed},
            "record_level_input_persisted": False,
            "synthetic_only": True,
        }
        return results, diagnostics, provenance

    def _sensitivity(self, payload: ComparativeAnalysisRequest) -> dict:
        rows: list[dict[str, Any]] = []
        if payload.psm.enabled:
            for caliper in payload.sensitivity.psm_calipers:
                for ratio in payload.sensitivity.psm_ratios:
                    result = self._psm(
                        payload.records,
                        payload.psm.model_copy(update={"caliper": caliper, "ratio": ratio}),
                    )
                    rows.append(
                        self._stability_row(
                            "PSM", {"caliper": caliper, "ratio": ratio}, result
                        )
                    )
        if payload.iptw.enabled:
            for truncation in payload.sensitivity.iptw_truncations:
                for stabilized in payload.sensitivity.iptw_stabilized:
                    result = self._iptw(
                        payload.records,
                        payload.iptw.model_copy(
                            update={
                                "truncation_percentiles": truncation,
                                "stabilized": stabilized,
                            }
                        ),
                    )
                    rows.append(
                        self._stability_row(
                            "IPTW",
                            {"truncation": truncation, "stabilized": stabilized},
                            result,
                        )
                    )
        return {
            "status": "computed_experimental",
            "rows": rows,
            "configuration_count": len(rows),
            "notice": "Sensitivity across specifications does not establish causal validity.",
        }

    @staticmethod
    def _stability_row(method: str, configuration: dict, result: dict) -> dict:
        return {
            "method": method,
            "configuration": configuration,
            "status": result.get("status"),
            "estimate": result.get("adjusted_risk_difference"),
            "confidence_interval": result.get("confidence_interval"),
            "n_or_ess": result.get("effective_sample_size")
            or result.get("matched_exposed_n"),
            "max_abs_smd": result.get("max_abs_smd"),
            "warnings": result.get("warnings", []),
        }

    def _table_one(
        self,
        exposed: list[SyntheticResearchRecord],
        comparator: list[SyntheticResearchRecord],
        covariates: list[str],
    ) -> dict:
        rows: list[dict] = []
        for name in covariates:
            raw_a = [item.covariates.get(name) for item in exposed]
            raw_b = [item.covariates.get(name) for item in comparator]
            nonmissing = [value for value in raw_a + raw_b if value is not None]
            numeric = bool(nonmissing) and all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in nonmissing
            )
            if numeric:
                a = [float(value) for value in raw_a if value is not None]
                b = [float(value) for value in raw_b if value is not None]
                rows.append(
                    {
                        "variable": name,
                        "type": "continuous",
                        "exposed": self._numeric_summary(a, len(raw_a)),
                        "comparator": self._numeric_summary(b, len(raw_b)),
                        "smd_before": _round(_continuous_smd(a, b)),
                    }
                )
                continue
            levels = sorted({str(value) for value in nonmissing})
            for level in levels:
                count_a = sum(str(value) == level for value in raw_a if value is not None)
                count_b = sum(str(value) == level for value in raw_b if value is not None)
                pa = count_a / len(exposed)
                pb = count_b / len(comparator)
                rows.append(
                    {
                        "variable": name,
                        "level": level,
                        "type": "categorical",
                        "exposed": {
                            "count": count_a,
                            "proportion": _round(pa),
                            "missing": sum(value is None for value in raw_a),
                        },
                        "comparator": {
                            "count": count_b,
                            "proportion": _round(pb),
                            "missing": sum(value is None for value in raw_b),
                        },
                        "smd_before": _round(_binary_smd(pa, pb)),
                    }
                )
        return {"exposed_n": len(exposed), "comparator_n": len(comparator), "rows": rows}

    @staticmethod
    def _numeric_summary(values: list[float], total: int) -> dict:
        if not values:
            return {"n": 0, "mean": None, "sd": None, "missing": total}
        return {
            "n": len(values),
            "mean": _round(fmean(values)),
            "sd": _round(_sample_sd(values)),
            "missing": total - len(values),
        }

    def _measures(
        self,
        exposed: list[SyntheticResearchRecord],
        comparator: list[SyntheticResearchRecord],
        denominator_unit: str,
        continuity_correction: float | None,
        threshold: int,
    ) -> dict:
        ae = sum(item.outcome for item in exposed)
        be = len(exposed) - ae
        ac = sum(item.outcome for item in comparator)
        bc = len(comparator) - ac
        suppressed = any(0 < count < threshold for count in (ae, be, ac, bc))
        if suppressed:
            return {
                "status": "suppressed",
                "reason": "small_cell",
                "threshold": threshold,
                "event_counts": {"exposed": None, "comparator": None},
                "derived_measures_withheld": True,
            }
        risk_e = ae / len(exposed)
        risk_c = ac / len(comparator)
        risk_difference = risk_e - risk_c
        rd_se = math.sqrt(
            risk_e * (1 - risk_e) / len(exposed)
            + risk_c * (1 - risk_c) / len(comparator)
        )
        cells = [float(ae), float(be), float(ac), float(bc)]
        correction_applied = False
        if 0 in cells:
            if continuity_correction is None:
                ratio_measures: dict[str, Any] = {
                    "status": "not_computable",
                    "reason": "zero_cell_requires_explicit_continuity_correction",
                }
            else:
                cells = [value + continuity_correction for value in cells]
                correction_applied = True
                ratio_measures = self._ratios(*cells)
        else:
            ratio_measures = self._ratios(*cells)
        person_days_e = sum(
            item.event_day if item.outcome and item.event_day is not None else item.follow_up_days
            for item in exposed
        )
        person_days_c = sum(
            item.event_day if item.outcome and item.event_day is not None else item.follow_up_days
            for item in comparator
        )
        factor = 365.25 if denominator_unit == "person_years" else 1.0
        pt_e = person_days_e / factor
        pt_c = person_days_c / factor
        incidence = {
            "status": "computed" if pt_e > 0 and pt_c > 0 else "not_computable",
            "reason": None if pt_e > 0 and pt_c > 0 else "non_positive_person_time",
            "unit": denominator_unit,
            "exposed_person_time": _round(pt_e),
            "comparator_person_time": _round(pt_c),
            "exposed_rate": _round(ae / pt_e) if pt_e > 0 else None,
            "comparator_rate": _round(ac / pt_c) if pt_c > 0 else None,
        }
        return {
            "status": "computed",
            "event_counts": {"exposed": ae, "comparator": ac},
            "non_event_counts": {"exposed": be, "comparator": bc},
            "risk": {"exposed": _round(risk_e), "comparator": _round(risk_c)},
            "risk_difference": {
                "estimate": _round(risk_difference),
                "confidence_interval": [
                    _round(risk_difference - 1.96 * rd_se),
                    _round(risk_difference + 1.96 * rd_se),
                ],
                "ci_method": "wald_normal_95",
            },
            "ratios": ratio_measures,
            "incidence": incidence,
            "continuity_correction": continuity_correction if correction_applied else None,
        }

    @staticmethod
    def _ratios(ae: float, be: float, ac: float, bc: float) -> dict:
        risk_e = ae / (ae + be)
        risk_c = ac / (ac + bc)
        rr = risk_e / risk_c
        rr_se = math.sqrt(1 / ae - 1 / (ae + be) + 1 / ac - 1 / (ac + bc))
        odds_ratio = (ae * bc) / (be * ac)
        or_se = math.sqrt(1 / ae + 1 / be + 1 / ac + 1 / bc)
        return {
            "status": "computed",
            "risk_ratio": {
                "estimate": _round(rr),
                "confidence_interval": [
                    _round(math.exp(math.log(rr) - 1.96 * rr_se)),
                    _round(math.exp(math.log(rr) + 1.96 * rr_se)),
                ],
                "ci_method": "log_wald_95",
            },
            "odds_ratio": {
                "estimate": _round(odds_ratio),
                "confidence_interval": [
                    _round(math.exp(math.log(odds_ratio) - 1.96 * or_se)),
                    _round(math.exp(math.log(odds_ratio) + 1.96 * or_se)),
                ],
                "ci_method": "log_wald_95",
            },
        }

    def _method_matrix(
        self,
        records: list[SyntheticResearchRecord],
        covariates: list[str],
    ) -> tuple[list[SyntheticResearchRecord], np.ndarray, np.ndarray, list[str], int]:
        complete = [
            item
            for item in records
            if all(item.covariates.get(name) is not None for name in covariates)
        ]
        dropped = len(records) - len(complete)
        if not complete or {item.group for item in complete} != {"exposed", "comparator"}:
            raise ComparativeAnalyticsError("Complete-case removeu um dos grupos.")
        feature_rows = [
            {name: item.covariates[name] for name in covariates} for item in complete
        ]
        vectorizer = DictVectorizer(sparse=False, sort=True)
        matrix = vectorizer.fit_transform(feature_rows)
        treatment = np.asarray([1 if item.group == "exposed" else 0 for item in complete])
        return complete, matrix, treatment, list(vectorizer.get_feature_names_out()), dropped

    def _fit_propensity(
        self,
        records: list[SyntheticResearchRecord],
        covariates: list[str],
        seed: int,
    ) -> tuple[list[SyntheticResearchRecord], np.ndarray, np.ndarray, np.ndarray, list[str], int]:
        complete, matrix, treatment, feature_names, dropped = self._method_matrix(
            records, covariates
        )
        model = make_pipeline(
            StandardScaler(),
            LogisticRegression(
                random_state=seed,
                solver="liblinear",
                max_iter=1000,
                fit_intercept=True,
            ),
        )
        try:
            model.fit(matrix, treatment)
        except ValueError as exc:
            raise ComparativeAnalyticsError(f"Propensity model não convergiu: {exc}") from exc
        logistic = model.named_steps["logisticregression"]
        if int(logistic.n_iter_[0]) >= 1000:
            raise ComparativeAnalyticsError("Propensity model atingiu limite de iterações.")
        probabilities = model.predict_proba(matrix)[:, 1]
        if np.any(~np.isfinite(probabilities)) or np.any(probabilities <= 0) or np.any(
            probabilities >= 1
        ):
            raise ComparativeAnalyticsError("Propensity degenerada (0/1 ou não finita).")
        return complete, matrix, treatment, probabilities, feature_names, dropped

    def _psm(self, records: list[SyntheticResearchRecord], config: PSMConfig) -> dict:
        try:
            complete, matrix, treatment, ps, features, dropped = self._fit_propensity(
                records, config.covariates, config.seed
            )
        except ComparativeAnalyticsError as exc:
            return {"status": "abstained", "reason": str(exc), "warnings": [str(exc)]}
        treated = [i for i, value in enumerate(treatment) if value == 1]
        controls = {i for i, value in enumerate(treatment) if value == 0}
        common_low = max(float(np.min(ps[treatment == 1])), float(np.min(ps[treatment == 0])))
        common_high = min(float(np.max(ps[treatment == 1])), float(np.max(ps[treatment == 0])))
        if common_low >= common_high:
            return {
                "status": "abstained",
                "reason": "no_common_support",
                "warnings": ["No propensity overlap; PSM não executado."],
            }
        pairs: list[tuple[int, int]] = []
        caliper_failures = 0
        for exposed_index in sorted(treated, key=lambda i: (float(ps[i]), complete[i].record_key)):
            candidates = sorted(
                controls,
                key=lambda i: (abs(float(ps[i] - ps[exposed_index])), complete[i].record_key),
            )
            selected = [
                item
                for item in candidates
                if abs(float(ps[item] - ps[exposed_index])) <= config.caliper
            ][: config.ratio]
            if len(selected) < config.ratio:
                caliper_failures += 1
                continue
            for item in selected:
                pairs.append((exposed_index, item))
                controls.remove(item)
        if not pairs:
            return {
                "status": "abstained",
                "reason": "no_matches_within_caliper",
                "warnings": ["Nenhum match dentro do caliper."],
            }
        matched_exposed = {exposed_index for exposed_index, _ in pairs}
        matched_comparators = {comparator_index for _, comparator_index in pairs}
        matched_indices = [index for pair in pairs for index in pair]
        matched_treatment = treatment[matched_indices]
        matched_matrix = matrix[matched_indices]
        balance = []
        for index, feature in enumerate(features):
            before = _continuous_smd(
                matrix[treatment == 1, index].tolist(), matrix[treatment == 0, index].tolist()
            )
            after = _continuous_smd(
                matched_matrix[matched_treatment == 1, index].tolist(),
                matched_matrix[matched_treatment == 0, index].tolist(),
            )
            balance.append(
                {"variable": feature, "smd_before": _round(before), "smd_after": _round(after)}
            )
        outcomes_e = [int(complete[e].outcome) for e, _ in pairs]
        outcomes_c = [int(complete[c].outcome) for _, c in pairs]
        after_values = [abs(item["smd_after"]) for item in balance if item["smd_after"] is not None]
        max_abs_smd = max(after_values, default=None)
        median_abs_smd = float(np.median(after_values)) if after_values else None
        propensity_distribution = {
            "exposed": [
                _round(float(item))
                for item in np.percentile(ps[treatment == 1], [5, 50, 95])
            ],
            "comparator": [
                _round(float(item))
                for item in np.percentile(ps[treatment == 0], [5, 50, 95])
            ],
            "percentiles": [5, 50, 95],
        }
        return {
            "status": "computed_experimental",
            "label": "PSM-adjusted research estimate",
            "estimand": "ATT",
            "algorithm": "nearest_neighbor_without_replacement",
            "library": METHOD_LIBRARY,
            "model": "logistic_regression",
            "encoding": "DictVectorizer one-hot",
            "normalization": config.normalization,
            "missing_data_policy": config.missing_data_policy,
            "intercept": True,
            "convergence": True,
            "seed": config.seed,
            "caliper": config.caliper,
            "ratio": config.ratio,
            "common_support": [_round(common_low), _round(common_high)],
            "matched_exposed_n": len(matched_exposed),
            "matched_comparator_n": len(matched_comparators),
            "unmatched_exposed_n": len(treated) - len(matched_exposed),
            "unmatched_comparator_n": len(controls),
            "dropped_missing_n": dropped,
            "caliper_failures": caliper_failures,
            "balance": balance,
            "max_abs_smd": _round(max_abs_smd),
            "median_abs_smd": _round(median_abs_smd),
            "propensity_distribution": propensity_distribution,
            "diagnostic_status": (
                "diagnostics acceptable"
                if max_abs_smd is not None and max_abs_smd <= 0.1
                else "diagnostics concerning"
            ),
            "adjusted_risk_difference": _round(fmean(outcomes_e) - fmean(outcomes_c)),
            "warnings": [
                "Balance improved ≠ no unmeasured confounding.",
                "Experimental synthetic-data research method; not a causal conclusion.",
            ],
        }

    def _iptw(self, records: list[SyntheticResearchRecord], config: IPTWConfig) -> dict:
        try:
            complete, matrix, treatment, ps, features, dropped = self._fit_propensity(
                records, config.covariates, config.seed
            )
        except ComparativeAnalyticsError as exc:
            return {"status": "abstained", "reason": str(exc), "warnings": [str(exc)]}
        exposed_ps = ps[treatment == 1]
        comparator_ps = ps[treatment == 0]
        common_low = max(float(np.min(exposed_ps)), float(np.min(comparator_ps)))
        common_high = min(float(np.max(exposed_ps)), float(np.max(comparator_ps)))
        if common_low >= common_high:
            return {
                "status": "abstained",
                "reason": "no_common_support",
                "warnings": ["No propensity overlap; IPTW não executado."],
            }
        prevalence = float(np.mean(treatment))
        if config.estimand == "ATE":
            weights = np.where(treatment == 1, 1 / ps, 1 / (1 - ps))
            if config.stabilized:
                weights = np.where(
                    treatment == 1, prevalence / ps, (1 - prevalence) / (1 - ps)
                )
        else:
            weights = np.where(treatment == 1, 1.0, ps / (1 - ps))
            if config.stabilized:
                weights = np.where(
                    treatment == 1,
                    prevalence,
                    prevalence * ps / (1 - ps),
                )
        if np.any(~np.isfinite(weights)):
            return {
                "status": "abstained",
                "reason": "non_finite_weights",
                "warnings": ["Pesos NaN/inf; IPTW não executado."],
            }
        truncated_count = 0
        truncation_values = None
        if config.truncation_percentiles:
            low, high = np.percentile(weights, config.truncation_percentiles)
            original = weights.copy()
            weights = np.clip(weights, low, high)
            truncated_count = int(np.sum(original != weights))
            truncation_values = [_round(float(low)), _round(float(high))]
        ess = float(np.sum(weights) ** 2 / np.sum(weights**2))
        if ess < 2 or ess < 0.1 * len(weights):
            return {
                "status": "abstained",
                "reason": "effective_sample_size_collapse",
                "effective_sample_size": _round(ess),
                "warnings": ["ESS colapsou; estimativa ajustada não produzida."],
            }
        balance = []
        for index, feature in enumerate(features):
            before = _continuous_smd(
                matrix[treatment == 1, index].tolist(), matrix[treatment == 0, index].tolist()
            )
            after = _weighted_smd(matrix[:, index], treatment, weights)
            balance.append(
                {"variable": feature, "smd_before": _round(before), "smd_after": _round(after)}
            )
        outcomes = np.asarray([int(item.outcome) for item in complete], dtype=float)
        risk_e = _weighted_mean(outcomes[treatment == 1], weights[treatment == 1])
        risk_c = _weighted_mean(outcomes[treatment == 0], weights[treatment == 0])
        percentiles = np.percentile(weights, [1, 5, 50, 95, 99])
        warnings = [
            "Residual confounding remains possible; not a causal conclusion.",
            "Experimental synthetic-data research method.",
        ]
        if float(np.max(weights)) > 10:
            warnings.append("Extreme weight warning: max weight exceeds 10.")
        after_values = [abs(item["smd_after"]) for item in balance if item["smd_after"] is not None]
        max_abs_smd = max(after_values, default=None)
        return {
            "status": "computed_experimental",
            "label": "IPTW-adjusted research estimate",
            "estimand": config.estimand,
            "library": METHOD_LIBRARY,
            "model": "logistic_regression",
            "stabilized": config.stabilized,
            "missing_data_policy": config.missing_data_policy,
            "seed": config.seed,
            "common_support": [_round(common_low), _round(common_high)],
            "weight_distribution": {
                "min": _round(float(np.min(weights))),
                "p01": _round(float(percentiles[0])),
                "p05": _round(float(percentiles[1])),
                "median": _round(float(percentiles[2])),
                "p95": _round(float(percentiles[3])),
                "p99": _round(float(percentiles[4])),
                "max": _round(float(np.max(weights))),
            },
            "truncation_percentiles": config.truncation_percentiles,
            "truncation_values": truncation_values,
            "truncated_count": truncated_count,
            "dropped_missing_n": dropped,
            "effective_sample_size": _round(ess),
            "balance": balance,
            "max_abs_smd": _round(max_abs_smd),
            "diagnostic_status": (
                "diagnostics acceptable"
                if max_abs_smd is not None and max_abs_smd <= 0.1 and float(np.max(weights)) <= 10
                else "diagnostics concerning"
            ),
            "adjusted_risk": {"exposed": _round(risk_e), "comparator": _round(risk_c)},
            "adjusted_risk_difference": _round(risk_e - risk_c),
            "warnings": warnings,
        }
