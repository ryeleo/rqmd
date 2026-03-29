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

Seed a small history chain and force one divergence:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-231=implemented
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-232=verified
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --undo
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --update REQ-PAG-233=blocked --blocked-note "manual QA divergence check"
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --timeline
```

### Step-by-step undo UX walkthrough

1. Launch interactive mode against the scratch corpus:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --screen-write
```

2. Open `requirements/page-24-edge-cases.md`, then open any of these requirements:
	- `REQ-PAG-231`
	- `REQ-PAG-232`
	- `REQ-PAG-233`

3. In the requirement action menu, confirm the footer shows:
	- `z=undo`
	- `y=redo`
	- `h=history`

4. Press `h` to open the history browser.

5. In the history browser, confirm the list is git-like rather than a plain summary list:
	- each row starts with `* <short-commit>`
	- the current head row includes a decoration like `(HEAD -> main)`
	- the command and reason appear in the one-line row
	- the right side shows timestamp and diff summary like `+1/-0 1f`

6. Select one history entry and confirm the detail pane shows:
	- branch
	- full commit
	- timestamp
	- reason
	- diff totals
	- changed files

7. Return to the requirement action menu with `u`.

8. Press `z` once.
	Expected:
	- the current catalog state moves to the previous history entry
	- the requirement panel refreshes instead of leaving stale text onscreen
	- if the undone change affected the currently open requirement, its status/metadata visibly changes

9. Press `y` once.
	Expected:
	- the undone change is reapplied
	- the requirement panel refreshes again
	- the footer and current-row marker remain stable after the redraw

10. Press `h` again after undo/redo and confirm the history browser still highlights the current head row.

11. Repeat the same flow once with `--no-screen-write`.
	 Expected:
	 - the same keys work
	 - output remains readable in append mode
	 - no crashes or duplicated rows appear while moving between requirement panel and history browser

### Expected outcomes

- `--history` output shows reason text and compact diff summaries.
- `--timeline` shows at least one `recovery-*` branch after the divergent blocked update.
- Interactive history rows look like a familiar git one-line log view.
- Undo and redo change the working catalog state, not just the displayed menu text.
- Opening history after undo/redo reflects the new current head correctly.

Confirmation guardrail check:

- Pick a recovery branch name from `--history` output and test both commands:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history-discard-branch <branch>
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history-discard-branch <branch> --force-yes --as-json
```

Expected:

- First command requires explicit confirmation.
- Forced command discards branch and returns `"discarded": true`.

Optional branch-checkout follow-up:

```bash
uv run rqmd --project-root test-corpus/scratch --docs-dir requirements --history-checkout-branch <branch>
```

Expected:

- The named branch becomes the current branch/head.
- Re-running `--history` or reopening the interactive history browser shows the checked-out branch at head.

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
