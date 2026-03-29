# Scratch Frontend QA Checklist

Use this checklist while running rqmd against this corpus.

## Launch Setup

From repository root:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements
```

Run explicit render mode checks:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --screen-write
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --no-screen-write
```

## Interactive Navigation

Run these manually in the menu UI:

- Page forward/back (`n` / `p`) repeatedly across all pages.
- Refresh (`r`) after changing one requirement in another terminal.
- Cycle sort columns (`s`) and direction (`d`) on file list and criterion list.
- Confirm current selection stays visible and stable while paging.
- Confirm footer legend remains fixed and does not push content upward.

Expected quick checks:

- No duplicated rows during redraw.
- No leftover ANSI artifacts after paging.
- Long title rows remain readable enough to identify the active item.

## Resize and Terminal Behavior

While menu is open:

- Resize terminal wider and narrower several times.
- Resize quickly during key navigation.
- Confirm menu does not crash and cursor focus remains sane.

Non-TTY fallback check:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --screen-write | cat
```

Expected:

- No full-screen clear/home escape behavior in piped mode.
- Output remains readable plain-text list formatting.

## Data/Metadata Rendering

Use this edge-case file for focused checks:

- requirements/page-24-edge-cases.md

Verify primarily in interactive mode (human QA), with optional spot checks:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --sub-domain query --as-tree
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --status blocked --as-tree
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --has-link --as-tree
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --priority p0 --as-tree
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --flagged --as-tree
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --no-flag --as-tree
```

Expected:

- `Blocked` and `Deprecated` reasons persist exactly.
- `Priority`, `Flagged`, and `Links` metadata show up consistently.
- Sub-domain filters isolate `Query API` vs `Mutation API` sections.

## Undo/History UI-adjacent Checks

Create two edits and test branch behavior:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-231=implemented
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-232=verified
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --undo
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-233=blocked
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --timeline
```

Confirmation guardrail check:

- Pick a recovery branch name from `--history` output and test both commands:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history-discard-branch <branch>
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history-discard-branch <branch> --force-yes --as-json
```

Expected:

- First command requires explicit confirmation.
- Forced command discards branch and returns `"discarded": true`.

Optional machine-readable spot checks (automation-oriented, not primary manual QA):

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history --as-json
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --timeline --as-json
```

## Quick Reset

If you want to restore corpus files after experimentation:

```bash
git restore test-corpus/scratch
```
