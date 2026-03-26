# Testing

This folder uses a pytest suite to validate implemented requirement behavior.

## Run Tests

From scripts/ac-cli:

```bash
uv run pytest -q
```

One-command local smoke check:

```bash
bash scripts/local-smoke.sh
```

## Latest Local Result

- 30 passed in 0.21s
- Command: `uv run pytest -q`

## Coverage Map

- tests/test_core_engine.py:
  - REQMD-CORE-001..010
- tests/test_automation_api.py:
  - REQMD-AUTOMATION-001..009
- tests/test_interactive_and_colors.py:
  - REQMD-INTERACTIVE-001..009, REQMD-INTERACTIVE-006A, REQMD-INTERACTIVE-006B
- tests/test_portability_packaging_docs.py:
  - REQMD-PORTABILITY-001..005
  - REQMD-PACKAGING-001..005

## Notes

- Proposed criteria are intentionally not treated as hard pass/fail requirements in this suite.
- Header IDs can use AC/R or custom prefixes when explicitly configured.
- This suite is designed to be copied with the package to new repositories.
- CI workflow: `.github/workflows/pytest.yml` runs this suite on push and pull_request.
