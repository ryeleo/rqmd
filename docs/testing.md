# Testing

This folder uses a pytest suite to validate implemented requirement behavior.

## Run Tests

From scripts/rqmd:

```bash
uv run pytest -q
```

One-command local smoke check:

```bash
bash scripts/local-smoke.sh
```

## Latest Local Result

- 50 passed
- Command: `uv run pytest -q`

## Coverage Map

- tests/test_core_engine.py:
  - RQMD-CORE-001..012, RQMD-CORE-014, RQMD-CORE-015
  - Includes RQMD-CORE-006 (five-status summary order), RQMD-CORE-011/012 init scaffold behavior, and init key prompt/default handling
- tests/test_automation_api.py:
  - RQMD-AUTOMATION-001..009 fully verified
  - Includes check-only no-write behavior, single/bulk updates, JSONL/CSV/TSV batch modes, ID alias schema variants, row-level path+line validation errors, conflict guardrails, scoped disambiguation, filtered tree output, and summary table controls
- tests/test_interactive_and_colors.py:
  - RQMD-INTERACTIVE-001..009, RQMD-INTERACTIVE-006A, RQMD-INTERACTIVE-006B
- tests/test_portability_packaging_docs.py:
  - RQMD-PORTABILITY-001..005
  - RQMD-PACKAGING-001..005

## Notes

- Proposed criteria are intentionally not treated as hard pass/fail requirements in this suite.
- Header IDs can use AC/R/RQMD defaults, custom prefixes via `--id-prefix`, or auto-detection from requirements index + linked domain docs.
- This suite is designed to be copied with the package to new repositories.
- CI workflow: `.github/workflows/pytest.yml` runs this suite on push and pull_request.
