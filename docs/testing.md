# Testing

This folder uses a pytest suite to validate implemented acceptance criteria behavior.

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
  - AC-ACCLI-CORE-001..010
- tests/test_automation_api.py:
  - AC-ACCLI-AUTOMATION-001..009
- tests/test_interactive_and_colors.py:
  - AC-ACCLI-INTERACTIVE-001..009, AC-ACCLI-INTERACTIVE-006A, AC-ACCLI-INTERACTIVE-006B
- tests/test_portability_packaging_docs.py:
  - AC-ACCLI-PORTABILITY-001..005
  - AC-ACCLI-PACKAGING-001..005

## Notes

- Proposed criteria are intentionally not treated as hard pass/fail requirements in this suite.
- This suite is designed to be copied with the package to new repositories.
- CI workflow: `.github/workflows/pytest.yml` runs this suite on push and pull_request.
