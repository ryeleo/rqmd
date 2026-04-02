# Brainstorm

## Discovery Mode

Explore vs Discovery... What is the difference...

Exploring is open ended, breadth focused, and doesn't have an end result required. It can be what it can be.

Discovery is more focused on finding specific information or insights that can help drive key decisions for the project. It has a goal of uncovering something helpful . It can be what it needs to be to achieve that result, but the result is the point.

Solving is more focused on a specific question or problem that might/could have a solution.



## Consistent AI Experience with rqmd-agents

We want rqmd agents to behave similarly in each project they are added to. They should provide similar outputs and follow similar workflows across projects, even if the underlying requirement content and priorities differ. This consistency helps users build trust and familiarity with the AI features, and it allows us to create reusable documentation, training materials, and best practices that apply broadly.

### AI output should use "info" "note" and "warning" block quotes like in our README.md

### AI output should use consistent emoji and status formatting for proposed/implemented/verified/blocked/deprecated items, matching the README guidance



# Brainstorm Triage

This file is now a checkpointed backlog scratchpad rather than a raw dump. Ideas that are already shipped or already tracked should move out of the way quickly so the remaining notes are easier to act on.

## Already tracked or shipped

- Nicer missing-doc startup guidance: `RQMD-CORE-009`.
- Project-specific ID-key recommendation during AI init: `RQMD-AI-031`.
- `rqmd all` positional overview: `RQMD-AUTOMATION-036`.
- Rank metadata and rank-first backlog grooming: `RQMD-SORTING-012` through `RQMD-SORTING-016`, plus `RQMD-INTERACTIVE-028` and `RQMD-INTERACTIVE-029`.
- Duplicate IDs fail fast and next-ID allocation already exist: `RQMD-CORE-026`, `RQMD-CORE-027`, and `RQMD-CORE-028`.
- External links, blocked-by linking, and global key renaming: `RQMD-CORE-021`, `RQMD-CORE-022`, and `RQMD-CORE-023`.
- README generation from requirement docs: `RQMD-CORE-024`.
- User-story terminology and dual user-story + Given/When/Then guidance: `RQMD-PORTABILITY-019`, `RQMD-AI-034`, and `RQMD-CORE-031`.
- AI workflow split between brainstorm and implement modes: `RQMD-AI-014` and `RQMD-AI-015`.
- Agent/skill instruction install bundle: `RQMD-AI-012`.
- Combinable filter semantics and `--update-flagged`: `RQMD-AUTOMATION-025`, `RQMD-AUTOMATION-032`, `RQMD-AUTOMATION-034`, and `RQMD-AUTOMATION-035`.
- Screen-write vs scrolling UI: `RQMD-UI-001` and `RQMD-UI-003`.
- Undo/redo with persistent history: `RQMD-UNDO-001` and `RQMD-UNDO-002`.
- `ReqMD` rename exploration: `RQMD-PACKAGING-012`.
- JSON schema versioning: `RQMD-AUTOMATION-033`.

## Newly promoted from this pass

- `RQMD-AI-036`: long-running priority-first development agent (`rqmd-dev-longrunning`).
- `RQMD-AI-037`: easy-first low-hanging-fruit development agent (`rqmd-dev-easy`).
- `RQMD-CORE-033`: versioned requirement markdown schema and migration path.
- `RQMD-CORE-034`: guided duplicate-ID repair workflow.
- `RQMD-SORTING-016`: positional `rqmd ranked` target for backlog grooming.
- `RQMD-INTERACTIVE-032`: grapheme-safe menu alignment for emoji-rich labels like `⚠️ Janky`.

## Clarified notes

### Startup UX

The bare `rqmd` no-docs startup path should stay requirement-driven and point users at the current canonical onboarding flow.

Desired behavior:

```text
$ rqmd

No requirement docs found. Expected to find docs/requirements/README.md or requirements/README.md.

First time setup?

- AI-driven (recommended): run `rqmd init`, then paste the generated prompt into your AI chat to get started.
- Manual / compatibility: run `rqmd init --scaffold` to create starter requirement docs directly.
```

### SSVR custom-status failure note

The `Speed Shooting VR` status issue is not a generic parser incompatibility. It only fails when rqmd is pointed at `test-corpus/SSVR/requirements` while the project root stays at this repository, which means the corpus-local `.rqmd.yml` is not loaded. If we want cross-root `--docs-dir` flows to auto-discover a neighboring config, that is a separate future requirement.

## Still worth triaging later

- Add even more agent-opinionated interview/prompt payload hints, for example `render_as_checkbox_prompt`, `do_not_summarize_after_each_answer`, or similar explicit downstream UX knobs.
- Improve terminal markdown rendering beyond the current lightweight bold/headings support.
- Consider explicit `Ctrl+Z` / `Ctrl+Y` bindings on top of the existing undo/redo feature set.
- Decide whether README generation should eventually become a stronger "tool-owned index" policy rather than marker-bounded sync.
- Explore whether cross-root config discovery should follow `--docs-dir` targets when users intentionally point rqmd at another repository's requirement catalog.
- Revisit native acceleration later if the current Python implementation becomes a real bottleneck despite the existing optional speedups path.

## Workflow prompt note

The "implement all proposed items" style prompt still works well, but the shipped rqmd AI workflow deliberately prefers small validated batches with re-triage between batches instead of one giant uninterrupted backlog sweep.

