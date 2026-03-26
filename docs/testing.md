# Testing

This folder uses a pytest suite to validate implemented requirement behavior.

## Run Tests

From scripts/reqmd:

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
  - REQMD-CORE-001..012, REQMD-CORE-014, REQMD-CORE-015
  - Includes REQMD-CORE-006 (five-status summary order), REQMD-CORE-011/012 init scaffold behavior, and init key prompt/default handling
- tests/test_automation_api.py:
  - REQMD-AUTOMATION-001..009 fully verified
  - Includes check-only no-write behavior, single/bulk updates, JSONL/CSV/TSV batch modes, ID alias schema variants, row-level path+line validation errors, conflict guardrails, scoped disambiguation, filtered tree output, and summary table controls
- tests/test_interactive_and_colors.py:
  - REQMD-INTERACTIVE-001..009, REQMD-INTERACTIVE-006A, REQMD-INTERACTIVE-006B
- tests/test_portability_packaging_docs.py:
  - REQMD-PORTABILITY-001..005
  - REQMD-PACKAGING-001..005

## Notes

- Proposed criteria are intentionally not treated as hard pass/fail requirements in this suite.
- Header IDs can use AC/R/REQMD defaults, custom prefixes via `--id-prefix`, or auto-detection from requirements index + linked domain docs.
- This suite is designed to be copied with the package to new repositories.
- CI workflow: `.github/workflows/pytest.yml` runs this suite on push and pull_request.
