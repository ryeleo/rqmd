# Testing

This folder uses a pytest suite to validate implemented requirement behavior.

## Run Tests

From scripts/rqmd:

```bash
uv run --extra dev pytest -q
```

The test suite requires `pytest-timeout` and will abort immediately if the dev extras are not installed.
If you prefer a synced environment, `uv sync --extra dev` also works before running pytest.
Global pytest timeout is capped at `30` seconds, and a few interactive-heavy regressions use tighter per-test markers.

One-command local smoke check:

```bash
bash scripts/local-smoke.sh
```

## Latest Local Result

- 143 passed
- Command: `uv run --extra dev pytest -q`

## Coverage Map

- tests/test_core_engine.py:
  - RQMD-CORE-001..012, RQMD-CORE-014, RQMD-CORE-015, RQMD-CORE-019, RQMD-CORE-020
  - Includes RQMD-CORE-006 (five-status summary order), RQMD-CORE-009 missing-docs init flow (`--force-yes`), RQMD-CORE-011/012 init scaffold behavior, and init key prompt/default handling
- tests/test_automation_api.py:
  - RQMD-AUTOMATION-001..009 fully verified
  - RQMD-ROLLUP-001, RQMD-ROLLUP-005, RQMD-ROLLUP-007
  - Includes check-only no-write behavior, single/bulk updates, JSONL/CSV/TSV batch modes, ID alias schema variants, row-level path+line validation errors, conflict guardrails, scoped disambiguation, filtered tree output, and summary table controls
- tests/test_interactive.py:
  - RQMD-INTERACTIVE-001..009, RQMD-INTERACTIVE-009A, RQMD-INTERACTIVE-011
  - RQMD-SORTING-003..011
  - Includes default interactive entry, single-key navigation, paging, next/prev history, direct lookup, reason prompts, write-permission preflight, sort strategies, refresh preservation, active-column indicators, and legend direction updates
- tests/test_priority_features.py:
  - RQMD-PRIORITY-004..007, RQMD-PRIORITY-009
  - Includes `--update-priority`, `--focus-priority`, `--priority`, `--seed-priorities`, priority summary generation, and priority sorting entry points
- tests/test_portability_packaging_docs.py:
  - RQMD-PORTABILITY-001..005, RQMD-PORTABILITY-008..010, RQMD-PORTABILITY-014
  - RQMD-PACKAGING-001..009
  - RQMD-CORE-013
- tests/test_performance.py:
  - RQMD-PORTABILITY-016
  - Includes deterministic scaling checks over 100/1000/10000 synthetic requirements and UI-009-aligned menu-render latency guardrail checks for <=80 rows.

## Notes

- Proposed requirements are intentionally not treated as hard pass/fail requirements in this suite.
- Header IDs can use AC/R/RQMD defaults, custom prefixes via `--id-namespace`, or auto-detection from requirements index + linked domain docs.
- This suite is designed to be copied with the package to new repositories.
- CI workflow: `.github/workflows/pytest.yml` runs this suite on push and pull_request.
