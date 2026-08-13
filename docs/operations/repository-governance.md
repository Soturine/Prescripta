# Repository governance

## Protected history

`main` uses the active repository ruleset **Protect main history** (ID `20778940`), which blocks deletion and non-fast-forward updates. It intentionally does not require pull requests, so the documented direct-main release workflow remains possible through normal pushes.

Version tags matching `v*` use **Protect version tags** (ID `20778941`), which blocks deletion and non-fast-forward movement. Creation remains allowed. A release tag must be annotated, point to the exact validated SHA, and must never be moved or recreated.

The obsolete remote branches `feat/v0.8.1-product-readiness` and `feat/v0.8.2-protocols-frontend-polish` had zero commits unique from `main` and were removed before v0.9.3.

## Release gates

The release candidate is validated once locally. The final `main` SHA is pushed normally, then CI, Security and Container Smoke must succeed for that exact SHA. Only afterward may the annotated tag be created. Tag workflows reuse the exact-SHA artifacts and attestations; they do not rebuild heavy gates.

Dependabot PRs are inspection-only. Maintainers reproduce an accepted update locally, test it, and commit it independently; bot branches are never merged or cherry-picked. Recovery after a tag is a new corrective release, never a moved tag.
