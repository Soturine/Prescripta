from __future__ import annotations

import argparse
import json
from pathlib import Path


def percentage(covered: int, total: int) -> float:
    return 100.0 if total == 0 else covered * 100.0 / total


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate independent coverage ratchets.")
    parser.add_argument("coverage", type=Path)
    parser.add_argument("--combined", type=float, required=True)
    parser.add_argument("--branches", type=float, required=True)
    args = parser.parse_args()

    totals = json.loads(args.coverage.read_text(encoding="utf-8"))["totals"]
    statements = int(totals["num_statements"])
    covered_statements = int(totals["covered_lines"])
    branches = int(totals["num_branches"])
    covered_branches = int(totals["covered_branches"])
    combined = percentage(covered_statements + covered_branches, statements + branches)
    branch_rate = percentage(covered_branches, branches)

    print(f"Backend coverage: combined={combined:.2f}% branches={branch_rate:.2f}%")
    failures = []
    if combined + 1e-9 < args.combined:
        failures.append(f"combined {combined:.2f}% < {args.combined:.2f}%")
    if branch_rate + 1e-9 < args.branches:
        failures.append(f"branches {branch_rate:.2f}% < {args.branches:.2f}%")
    if failures:
        raise SystemExit("Coverage ratchet failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
