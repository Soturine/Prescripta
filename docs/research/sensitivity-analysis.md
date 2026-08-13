# Sensitivity analysis

The v0.9.3 comparative engine runs bounded, deterministic specification grids over the existing experimental PSM and IPTW implementations. PSM varies caliper and matching ratio; IPTW varies truncation percentiles and stabilization. Every row records configuration, estimate/status, sample diagnostics and a stable content hash.

The default limits are eight values per dimension. The engine does not select the most favorable estimate and does not convert stability into causal validity. Poor overlap, remaining standardized mean differences, low effective sample size, missingness, positivity concerns and residual/unmeasured confounding remain explicit limitations.

An independently generated synthetic fixture uses SciPy optimization and direct weight formulas without importing the production engine. Tests compare propensity scores, ATE/ATT weights and effective sample size under a declared tolerance. This validates the implemented numerical contract only; it is not external epidemiological validation.
