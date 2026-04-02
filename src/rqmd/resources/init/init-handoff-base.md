You are helping initialize rqmd in the repository at {{REPO_ROOT}}.

1. Run `{{INIT_COMMAND}}`.
2. If your terminal wrapper truncates stdout, rerun it as `{{INIT_ARTIFACT_COMMAND}}` and read that file directly.
3. Read the JSON payload and report which init strategy was selected.
4. If `interview.question_groups` is present, switch into an interactive one-question-at-a-time multi-choice interview instead of paraphrasing the payload.
5. Start any `option_annotations.default_checked_values` as already selected, allow custom answers only when the question says so, and avoid recapping all prior answers after each question unless the user asks.
6. Collect the interview answers first, then rerun the same init command with repeated `--answer FIELD=VALUE` entries to apply them.
7. Review the proposed files with the user before writing anything.
8. Apply only after explicit confirmation by running `{{APPLY_COMMAND}}`.
