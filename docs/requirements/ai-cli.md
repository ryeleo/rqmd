# AI CLI Requirement

Scope: a companion rqmd-ai CLI for AI-oriented requirement workflows that are distinct from the shared automation contract, including prompt-context export, guarded apply flows, onboarding guidance, and auditability over rqmd-managed docs.

<!-- acceptance-status-summary:start -->
Summary: 1💡 20🔧 0✅ 0⛔ 3🗑️
<!-- acceptance-status-summary:end -->

### RQMD-AI-001: Dedicated rqmd-ai entrypoint
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a rqmd user when AI-assisted requirement work is needed
- I want a dedicated rqmd-ai command in this package
- So that AI workflows are explicit and separate from core rqmd interactive editing behavior.

### RQMD-AI-002: Read-only by default
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a safety-focused user when running AI operations
- I want rqmd-ai to default to read-only planning/reporting
- So that no requirement files are modified unless an explicit write/apply mode is requested.

### RQMD-AI-003: Deterministic machine output mode
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- As an automation user when integrating with CI or bots
- I want rqmd-ai --json to emit a stable schema with deterministic ordering
- So that downstream tooling can parse and diff outputs reliably.
- Superseded by `RQMD-AUTOMATION-010`, `RQMD-AUTOMATION-011`, `RQMD-AUTOMATION-012`, and `RQMD-AUTOMATION-013`, which should define the shared machine-output contract for both `rqmd` and any future `rqmd-ai` surface.

### RQMD-AI-004: Requirement context export for prompts
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As an AI operator when preparing model prompts
- I want rqmd-ai to export selected requirement context by ID/file/status
- So that prompts can include only relevant requirement slices with stable identifiers.

### RQMD-AI-005: Patch-plan preview before apply
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a maintainer when AI suggests doc updates
- I want rqmd-ai to provide a patch preview and change summary first
- So that humans can review intended modifications before any write occurs.

### RQMD-AI-006: Apply mode with guardrails
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a repository owner when enabling AI writes
- I want rqmd-ai --write to enforce strict validation and conflict checks
- So that malformed edits, unknown IDs, and cross-file ambiguity are rejected safely.

### RQMD-AI-007: Teaching-oriented guidance output
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a team lead when onboarding contributors and AI agents
- I want rqmd-ai to output concise guidance on requirement conventions and status workflow
- So that both humans and AI systems learn the expected rqmd contract quickly.
- So that init-scaffold copy, README guidance, and first-run instructions are strong enough to support AI-friendly onboarding from day one.

### RQMD-AI-008: Batch suggestion ingestion
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- As an automation user when importing AI suggestions from external systems
- I want rqmd-ai to accept JSONL/CSV suggestion files
- So that recommendation pipelines can be processed in deterministic batches.
- Superseded by `RQMD-AUTOMATION-004` and `RQMD-AUTOMATION-015` until `rqmd-ai` defines an input schema that is materially different from the shared batch automation model.

### RQMD-AI-009: Explicit non-interactive guarantee
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- As a CI user when running headless jobs
- I want rqmd-ai modes to avoid interactive prompts unless explicitly requested
- So that jobs never hang waiting for terminal input.
- Superseded by `RQMD-AUTOMATION-017`, which should remain the single source of truth for prompt-suppression behavior across machine-oriented CLI modes.

### RQMD-AI-010: End-to-end audit report
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a compliance-oriented user when AI modifies requirements
- I want rqmd-ai to emit a structured audit record of inputs, decisions, and outputs
- So that AI-assisted requirement changes remain traceable and reviewable.
- So that emitted audit records are sourced from the same local `rqmd-history` backend defined by `RQMD-UNDO-005` and `RQMD-UNDO-011`, rather than a parallel audit store.

### RQMD-AI-011: Domain-body context export for prompts
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As an AI operator preparing prompts with domain-level context
- I want rqmd-ai exports to optionally include domain-body content aligned with RQMD-CORE-019
- So that model prompts can include architecture/rationale notes without embedding those notes into individual requirement bodies.
- So that domain-body inclusion is explicit and bounded (for example size-capped or section-filtered) to keep prompt payloads stable and cost-aware.

### RQMD-AI-012: Installable AI agent/skill instruction bundle
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a team maintainer when onboarding AI-assisted contributors
- I want rqmd to install a standard agent/skill instruction bundle into the workspace
- So that AI agents have a consistent contract for JSON modes, workflow sequencing, and requirement/doc update expectations
- So that installation supports a dry-run preview and idempotent re-run behavior
- So that teams can choose a minimal or full preset while preserving existing customized instruction files unless explicit overwrite is requested
- So that installed guidance references local commands and requirement file conventions in this repository layout.

### RQMD-AI-013: Requirement-first AI workflow guidance
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer when handing brainstorm items to an AI agent
- I want rqmd-ai guidance and docs to prescribe a requirement-first workflow before code is applied
- So that brainstorm ideas are promoted into tracked requirements, index updates, and changelog entries before implementation starts.
- So that the recommended loop stays explicit: export focused context, update requirements/docs, preview the patch, apply only with explicit write mode, and run verification afterward.

### RQMD-AI-014: Brainstorm-to-requirements planning mode
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer when early planning lives in `docs/brainstorm.md` or similar scratch notes
- I want rqmd-ai to support a dedicated brainstorm workflow that turns raw notes into ranked requirement proposals
- So that loose brainstorming can be promoted into concrete requirement entries before implementation begins.
- So that the workflow can recommend target requirement documents, proposed IDs, statuses, and priorities without applying code changes.
- So that `rqmd-ai --workflow-mode brainstorm` reads `docs/brainstorm.md` by default and can also accept a custom markdown note file via `--brainstorm-file`.

### RQMD-AI-015: Proposal-batch implementation mode
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a maintainer when asking an AI agent to execute backlog work
- I want rqmd-ai guidance to define an explicit implement mode that works the highest-priority proposed requirements in small validated batches
- So that the agent updates requirements, tests, and changelog entries as details become concrete rather than deferring documentation until the end.
- So that each batch re-checks that `rqmd` still runs, the test suite passes, and the remaining proposal priorities are reviewed before continuing.
- So that `rqmd-ai --workflow-mode implement` exposes this loop as an explicit read-only guide payload instead of burying it in generic onboarding text.

### RQMD-AI-016: Resource-backed AI UX source of truth
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer evolving rqmd-ai onboarding and workflow guidance
- I want the user-facing AI UX text for rqmd-ai to be sourced from editable package resource markdown/metadata instead of embedded Python constants
- So that workflow summaries, examples, validation checks, and other guide text can be updated in one central resources/bundle location without code edits.
- So that the shipped bundle skill files act as the primary editable source of truth for the AI guidance experience exposed by rqmd-ai.

### RQMD-AI-017: Default bundled skill-definition export when bundle is absent
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer or AI operator invoking rqmd-ai in a workspace that has not installed the rqmd bundle
- I want default rqmd-ai output to include the packaged skill and agent YAML/markdown definitions directly from resources
- So that an AI consumer can bootstrap from the shipped definitions immediately without requiring a prior bundle-install step.
- So that the default guidance payload can surface the exact resource-backed skill contracts that rqmd ships, rather than only summarizing them indirectly.

### RQMD-AI-018: Bundle-aware suppression of duplicate default skill exports
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a user running rqmd-ai in a workspace where the rqmd bundle is already installed
- I want rqmd-ai to detect the installed bundle and avoid redundantly embedding the packaged skill and agent definitions in default output
- So that guidance stays concise and does not duplicate definitions that are already present in the local workspace.
- So that bundle-aware default output can still explain which local skill or agent files are active without emitting the full packaged definitions again.

### RQMD-AI-019: Project-specific dev and test skill scaffolding
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer installing the rqmd AI bundle into a real project
- I want bundle bootstrap to help generate project-local `dev` and `test` skills tailored to that repository's actual commands and workflows
- So that the installed `rqmd-dev` agent can delegate build, run, smoke-test, and test behavior to project-specific skills instead of relying on generic assumptions.
- So that generated skill definitions can capture the repository's actual build/test/smoke commands, validation expectations, and any required environment setup.
- So that teams can review and edit those generated skill files after bootstrap rather than keeping that project knowledge buried in agent prose.

### RQMD-AI-020: Agent-driven bundle bootstrap chat
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a maintainer onboarding AI workflows in a new repository
- I want the rqmd bundle bootstrap flow to be driveable through an AI-guided chat session
- So that bundle install can interview the user about the project's build, run, dev, and test commands instead of forcing all customization through manual file edits.
- So that the bootstrap chat can propose `dev` and `test` skill content, preview the generated files, and only write them after explicit review.
- So that teams can adopt the bundle through a guided conversation even when they have not yet learned the exact customization file formats.

### RQMD-AI-021: rqmd-dev delegation to project dev and test skills
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer using the installed `rqmd-dev` agent in a repository with project-local AI skills
- I want `rqmd-dev` guidance to explicitly depend on repository-specific `dev` and `test` skills when they exist
- So that implementation agents know where to find the canonical project commands for building, running, smoke-testing, and validating the work under development.
- So that `rqmd-dev` can stay generally reusable while still becoming concretely useful once a repository has generated or customized those project-local skills.

### RQMD-AI-022: Legacy-repo init skill and workflow
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer introducing rqmd into a repository that has never used it before
- I want an `init-legacy` AI skill or workflow that helps bootstrap rqmd from the repository's existing reality
- So that adoption can start from the current codebase, docs, backlog, and conventions instead of requiring a blank-slate scaffold.
- So that rqmd-ai can guide the user through a legacy-init flow focused on first-use setup rather than generic bundle installation alone.

### RQMD-AI-023: Useful first-pass requirements folder for legacy repos
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer initializing rqmd in an established repository
- I want the legacy-init flow to produce a useful first-pass `requirements/` folder that I can immediately start editing and using
- So that the resulting requirements docs reflect the repository's current product areas, workflows, and likely work streams instead of only a generic starter example.
- So that the flow can propose an initial requirements structure, starter domain files, and seed content for review before writing.

### RQMD-AI-024: Optional GitHub issue discovery during legacy init
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer bootstrapping rqmd in a repository that uses GitHub issues
- I want the legacy-init workflow to try using `gh` to inspect repository issues when the GitHub CLI is available and authenticated
- So that rqmd can incorporate the existing issue backlog into its first-pass requirement suggestions instead of ignoring a major source of project intent.
- So that the workflow remains optional and graceful when `gh` is missing, unauthenticated, or the repository has no accessible issue data.
