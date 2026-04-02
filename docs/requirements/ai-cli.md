# AI CLI Requirement

Scope: a companion rqmd-ai CLI for AI-oriented requirement workflows that are distinct from the shared automation contract, including prompt-context export, guarded apply flows, onboarding guidance, and auditability over rqmd-managed docs.

<!-- acceptance-status-summary:start -->
Summary: 0💡 37🔧 2✅ 0⚠️ 0⛔ 3🗑️
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
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer onboarding AI workflows in a new repository
- I want the rqmd bundle bootstrap flow to be driveable through an AI-guided chat session
- So that bundle install can interview the user about the project's build, run, dev, and test commands instead of forcing all customization through manual file edits.
- So that the bootstrap chat can propose `dev` and `test` skill content, preview the generated files, and only write them after explicit review.
- So that teams can adopt the bundle through a guided conversation even when they have not yet learned the exact customization file formats.
- So that the bootstrap chat can present grouped multiple-choice suggestions, allow multi-select answers, let users skip sections, and accept custom text alongside the inferred commands.
- So that each interview option can carry richer UX hints such as recommended choices, detected-from provenance, and safe defaults.

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
- So that the legacy-init flow can reuse the same grouped interview UX as bundle bootstrap, including suggested choices, multi-select answers, and custom notes.
- So that legacy-init interview options can surface recommended choices, detected source provenance, and safe defaults for the generated starter catalog.

### RQMD-AI-023: Useful first-pass requirements folder for legacy repos
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer initializing rqmd in an established repository
- I want the legacy-init flow to produce a useful first-pass `requirements/` folder that I can immediately start editing and using
- So that the resulting requirements docs reflect the repository's current product areas, workflows, and likely work streams instead of only a generic starter example.
- So that the flow can propose an initial requirements structure, starter domain files, and seed content for review before writing.
- So that interview answers about catalog location, ID prefix, starter domains, docs review, and workflow commands can directly shape the generated starter catalog.

### RQMD-AI-024: Optional GitHub issue discovery during legacy init
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer bootstrapping rqmd in a repository that uses GitHub issues
- I want the legacy-init workflow to try using `gh` to inspect repository issues when the GitHub CLI is available and authenticated
- So that rqmd can incorporate the existing issue backlog into its first-pass requirement suggestions instead of ignoring a major source of project intent.
- So that the workflow remains optional and graceful when `gh` is missing, unauthenticated, or the repository has no accessible issue data.

### RQMD-AI-025: Init-chat AI handoff prompt generation
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer who wants another AI chat to drive rqmd init on my behalf
- I want `rqmd-ai` init workflows to emit a ready-to-paste handoff prompt for an external AI assistant
- So that I can start the guided bootstrap experience by pasting one concise prompt instead of manually explaining the expected command flow.
- So that the handoff prompt is tailored to the active workflow, such as bundle install onboarding versus legacy-init onboarding, instead of using one generic script.
- So that the handoff prompt tells the receiving AI to run the corresponding `rqmd-ai init --chat --json` or `rqmd-ai install --chat --json` command, inspect the interview payload, ask grouped follow-up questions, and rerun with `--answer` values before any write step.

### RQMD-AI-026: Concise copy/paste init prompt UX
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer invoking `rqmd-ai` init workflows directly in my terminal
- I want `rqmd-ai` to print a concise human-facing “paste this into your AI chat” prompt when requested
- So that the init-chat flow is understandable even when the user has not yet learned the JSON interview protocol.
- So that the output includes a short explanatory lead-in plus the exact copy/paste prompt text rather than only a large raw JSON payload.
- So that the generated prompt can mention the current repository path, the intended init/install mode, and the exact `rqmd-ai ... --chat --json` command the receiving AI should run.
- So that the prompt stays aligned with the richer grouped interview contract, including grouped questions, selectable suggestions, custom answers, and explicit write confirmation.

### RQMD-AI-027: Unified init workflow with heuristic routing
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer starting rqmd in a repository
- I want `rqmd-ai` to expose a single `init` workflow name instead of forcing me to choose between a "new" and "legacy" mental model up front
- So that init entry feels simple even when the tool needs to choose a different setup path behind the scenes.
- So that `rqmd-ai init` or `--workflow-mode init` can detect whether the repository already looks established and route to the appropriate bootstrap strategy using reasonable heuristics.
- So that the heuristic can consider signals such as existing source folders, test folders, README/docs volume, build metadata, and issue/backlog availability instead of only whether rqmd docs already exist.
- So that the chosen path is reported clearly in the payload and user-facing output rather than silently hiding which init strategy was selected.

### RQMD-AI-028: Explicit legacy-init compatibility and override flag
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer working in an unusual repository that may confuse bootstrap heuristics
- I want an explicit compatibility path to force legacy-style initialization when needed
- So that repositories with strange layouts or incomplete heuristics are still easy to initialize intentionally.
- So that rqmd-ai can keep a `--legacy` style override or equivalent explicit selector even after the main entrypoint is unified under `init`.
- So that existing `init-legacy` workflows can remain supported as a compatibility alias during a transition period instead of breaking current docs, prompts, or installed skills immediately.

### RQMD-AI-029: Chat-first init entrypoint for new projects
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer setting up rqmd in a new or existing repository with AI help
- I want `rqmd-ai init --chat` to be the canonical AI-facing onboarding entrypoint
- So that the recommended startup path is one clear command instead of a mix of `install`, `init-legacy`, and hand-written guidance.
- So that `rqmd-ai init --chat` emits the concise AI handoff prompt plus the machine-readable interview payload needed for a receiving chat agent to drive the rest of initialization.
- So that the command can route through the unified `init` heuristics and still report which strategy it selected for the repository.
- So that users who do want to stay fully inside terminal automation can still run explicit non-chat variants when needed.

### RQMD-AI-030: Default init guidance favors AI chat flow
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a new rqmd user who wants the fastest successful onboarding path
- I want the default help, onboarding guide output, and initialization hints to recommend the AI-chat workflow first
- So that the product teaches the strongest end-to-end flow by default instead of expecting users to discover it from scattered flags and examples.
- So that messages about initialization point users toward `rqmd init` or `rqmd-ai init --chat` as the primary path and relegate lower-level compatibility forms to secondary documentation.
- So that the suggested flow is explicit: run the init command, paste the generated prompt into an AI chat, answer the grouped interview, let the agent apply the bootstrap, and then begin refining the generated requirements catalog.

### RQMD-AI-031: Init interview recommends a project-specific ID prefix
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer initializing rqmd in a new or existing repository
- I want the `rqmd-ai init` interview to strongly recommend a short project-specific ID prefix instead of only generic fallbacks such as `REQ`, `RQMD`, or `AC`
- So that requirement IDs are easier to recognize, less likely to collide with other catalogs, and more meaningful in discussion and documentation.
- So that the init payload can still expose generic fallback prefixes, but clearly frame them as secondary options when a project-specific short key can be inferred or typed.
- So that the custom-answer guidance and prompt text make the project-specific recommendation obvious to any receiving AI or user reviewing the JSON interview payload.

### RQMD-AI-032: Init interview exposes default-checked suggested choices
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer reviewing the `rqmd-ai init` interview through another AI chat or structured prompt UI
- I want multi-select init questions to declare which suggested or recommended options should start checked by default
- So that users can plainly see what the workflow intends to pick unless they actively uncheck those defaults.
- So that the init payload does not force those values silently, but instead exposes explicit preselected choices alongside the existing recommended and safe-default metadata.
- So that receiving tools can render consistent multi-choice prompts where suggested or recommended init options begin selected while still allowing opt-out before any write step.

### RQMD-AI-033: Explicit interactive interview contract for receiving agents
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer pasting `rqmd-ai init --chat --json` output into another AI system
- I want the payload to explicitly declare that the receiver should switch into a structured interactive interview mode
- So that the receiving AI presents a real one-question-at-a-time multi-choice session instead of summarizing the JSON and asking for freeform answers after every step.
- So that the payload can expose machine-readable instructions for presentation style, checked-default behavior, rerun timing, and recap timing rather than leaving those behaviors implicit in `question_groups` alone.
- So that the payload can also expose a precomputed interview flow with ordered groups and questions, making the intended question order and UI style explicit for agents that do not want to infer it themselves.

### RQMD-AI-034: Encourage dual user-story and Given/When/Then requirement authoring
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a maintainer using `rqmd-ai` to draft, refine, or implement requirements
- I want rqmd-ai guidance and editing workflows to actively encourage requirements that include both a user story and a Given/When/Then acceptance block when both are useful
- So that generated or edited requirements are easier to understand at both the product-intent and implementation-detail levels.
- So that rqmd-ai can treat the two blocks as related views of the same requirement and help keep them semantically aligned instead of letting them drift silently.
- So that AI-facing prompts, review flows, and requirement-edit suggestions nudge contributors toward maintaining both blocks together rather than treating one style as disposable prose.

### RQMD-AI-035: Default markdown closeout styling for installed AI guidance
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a maintainer initializing rqmd AI guidance with `rqmd-ai init`
- I want the installed default agent instructions to prefer a concise markdown closeout structure such as `# What got done`, `# Up next`, and `# Direction`
- So that implementation updates are easier to scan quickly in AI chat transcripts and review handoffs.
- So that `What got done` summarizes the completed work in polished markdown instead of ad hoc prose.
- So that `Up next` includes the full markdown bodies of the highest-priority proposed requirements rather than only listing requirement IDs as rendered markdown and not code blocks -- do not put each requirement within "```" blocks!!!
- So that `Direction` gives a concrete next recommendation derived from the active backlog state instead of a vague generic follow-up.
- So that this formatting becomes the default style installed by `rqmd-ai init` while still allowing repositories to customize the final instructions after install.

### RQMD-AI-036: Long-running priority-first development agent
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer when I want an AI agent to keep working through the backlog for an extended session
- I want rqmd to ship a `rqmd-dev-longrunning` agent variant that explicitly tries to continue making progress for as long as feasible
- So that the agent works proposed requirements in priority order, keeps reassessing the backlog after each validated batch, and stops only when it reaches a real blocker, exhausts feasible work, or completes the active slice.
- So that the long-running mode remains requirement-first and still updates requirements, tests, verification results, and changelog entries as it goes instead of treating persistence as permission to skip quality gates.
- So that the guidance explicitly favors autonomous follow-through and repeated re-triage over early handoff when there is still clear work available.
- So that its outputs, closeout structure, and workflow language still feel recognizably rqmd across projects instead of becoming a project-specific one-off personality.

### RQMD-AI-037: Easy-first low-hanging-fruit development agent
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer when I want quick backlog progress without sending an AI agent into the hardest architectural work immediately
- I want rqmd to ship a `rqmd-dev-easy` agent variant that focuses on low-risk, high-confidence requirement slices first
- So that the agent preferentially picks low-hanging-fruit proposed requirements where it can make clean progress with minimal exploratory risk.
- So that the easy-first mode can still respect overall requirement priority order, but only within the subset of items that appear straightforward enough to implement, validate, and document in small batches.
- So that maintainers can choose between a broad long-running executor and a conservative easy-wins executor depending on how much autonomy or risk they want in a given session.
- So that the easy-first mode still follows the same core rqmd output conventions and workflow shape as other shipped agents even when its selection strategy differs.

### RQMD-AI-038: Legacy-init installs local schema guidance into generated requirement indexes
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer bootstrapping rqmd in an existing repository through `rqmd-ai init`
- I want the generated `docs/requirements/README.md` or `requirements/README.md` to include the current local rqmd schema guidance that AI agents need during follow-up work
- So that the initialized repository contains a nearby, tool-owned schema reference instead of forcing humans or AI agents to rely on memory, external docs, or a missing side file.
- So that legacy-init and other init apply paths install or embed the schema content deterministically as part of the generated requirements index experience rather than treating schema visibility as optional tribal knowledge.
- So that the generated requirements index clearly points at the local schema source of truth and keeps that source synchronized with the shipped rqmd contract templates.
- So that AI agents working only from local repository files can reliably discover the requirement markdown contract during later implementation and review sessions.

### RQMD-AI-039: Authored changelog maintenance skill
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer using the shipped rqmd AI bundle to prepare releases and pre-releases
- I want rqmd to ship a dedicated `/rqmd-changelog` skill for maintaining `CHANGELOG.md`
- So that changelog work becomes a first-class authored workflow instead of an implicit side effect of generic docs cleanup.
- So that top-level changelog entries stay focused on human-directed decisions, user-visible behavior, and other release-relevant changes instead of turning into a raw dump of every AI implementation step.
- So that supporting AI implementation detail can still be recorded under a nested heading such as `AI Development` when that context is useful without crowding the primary narrative.
- So that maintainers get consistent guidance for updating `Unreleased`, tightening noisy recent entries, and preserving Keep a Changelog structure across repositories that install the bundle.

### RQMD-AI-040: General documentation-quality skill
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer improving repository documentation with the shipped rqmd AI bundle
- I want rqmd to ship a dedicated `/rqmd-docs` skill for documentation quality and structure work beyond simple drift correction
- So that README, requirement docs, bundle guidance, and other markdown can be improved using explicit standards for headings, clarity, jargon handling, page splitting, hyperlinks, and callouts instead of only being kept mechanically in sync.
- So that `rqmd-doc-sync` can stay focused on alignment and follow-up cleanup after behavior changes rather than trying to own all documentation craft decisions.
- So that repositories installing the bundle get a reusable authored documentation workflow that is broader than changelog curation but more specific than generic implementation guidance.
- So that documentation improvements can stay technical but user-friendly, with readable structure and smaller linked pages when content grows too long.

### RQMD-AI-041: Consistent cross-project AI workflow experience
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer using rqmd agents across multiple repositories
- I want shipped rqmd agents and skills to behave consistently across projects even when the requirement catalogs and priorities differ
- So that users build trust and familiarity with the AI workflows instead of relearning a different style in every repository.
- So that outputs, closeout structure, status formatting, and workflow sequencing remain recognizably rqmd unless a repository intentionally overrides them.
- So that reusable documentation, training material, and best practices can describe one stable rqmd agent experience instead of many near-miss variants.
- So that project-local customization still fits inside a consistent shared contract rather than silently changing the overall workflow shape.

### RQMD-AI-042: Pinned context and decision notes workflow
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a maintainer or collaborator working with rqmd over multiple sessions
- I want an `rqmd-pin` workflow for capturing important context, decisions, and quick-reference notes that should remain easy to find later
- So that useful insights do not disappear into chat history or scattered documentation during brainstorming and implementation.
- So that the workflow can help teams choose an appropriate home for pinned notes, such as a dedicated markdown file, a README section, or a `docs/pins/` folder with one note per topic, defaulting to `docs/pins/` when the best location is unclear for maintainability.
- So that larger pin collections can grow into an indexed notes area without turning into another hard-to-navigate dump, with `/rqmd-docs` handling any follow-on structure and navigation cleanup when needed.
- So that pinned information can follow a readable, reviewable format instead of becoming ad hoc scratch text.
- So that rqmd can grow a lightweight memory or note-pinning workflow without forcing one storage layout on every repository.
