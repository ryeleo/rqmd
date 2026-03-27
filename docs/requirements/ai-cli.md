# AI CLI Requirement

Scope: a companion rqmd-ai CLI for AI-oriented requirement workflows that are distinct from the shared automation contract, including prompt-context export, guarded apply flows, onboarding guidance, and auditability over rqmd-managed docs.

<!-- acceptance-status-summary:start -->
Summary: 7💡 0🔧 0✅ 0⛔ 3🗑️
<!-- acceptance-status-summary:end -->

### RQMD-AI-001: Dedicated rqmd-ai entrypoint
- **Status:** 💡 Proposed
- As a rqmd user when AI-assisted requirement work is needed
- I want a dedicated rqmd-ai command in this package
- So that AI workflows are explicit and separate from core rqmd interactive editing behavior.

### RQMD-AI-002: Read-only by default
- **Status:** 💡 Proposed
- As a safety-focused user when running AI operations
- I want rqmd-ai to default to read-only planning/reporting
- So that no requirement files are modified unless an explicit write/apply mode is requested.

### RQMD-AI-003: Deterministic machine output mode
- **Status:** 🗑️ Deprecated
- As an automation user when integrating with CI or bots
- I want rqmd-ai --json to emit a stable schema with deterministic ordering
- So that downstream tooling can parse and diff outputs reliably.
- Superseded by `RQMD-AUTOMATION-010`, `RQMD-AUTOMATION-011`, `RQMD-AUTOMATION-012`, and `RQMD-AUTOMATION-013`, which should define the shared machine-output contract for both `rqmd` and any future `rqmd-ai` surface.

### RQMD-AI-004: Requirement context export for prompts
- **Status:** 💡 Proposed
- As an AI operator when preparing model prompts
- I want rqmd-ai to export selected requirement context by ID/file/status
- So that prompts can include only relevant requirement slices with stable identifiers.

### RQMD-AI-005: Patch-plan preview before apply
- **Status:** 💡 Proposed
- As a maintainer when AI suggests doc updates
- I want rqmd-ai to provide a patch preview and change summary first
- So that humans can review intended modifications before any write occurs.

### RQMD-AI-006: Apply mode with guardrails
- **Status:** 💡 Proposed
- As a repository owner when enabling AI writes
- I want rqmd-ai --apply to enforce strict validation and conflict checks
- So that malformed edits, unknown IDs, and cross-file ambiguity are rejected safely.

### RQMD-AI-007: Teaching-oriented guidance output
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a team lead when onboarding contributors and AI agents
- I want rqmd-ai to output concise guidance on requirement conventions and status workflow
- So that both humans and AI systems learn the expected rqmd contract quickly.
- So that init-scaffold copy, README guidance, and first-run instructions are strong enough to support AI-friendly onboarding from day one.

### RQMD-AI-008: Batch suggestion ingestion
- **Status:** 🗑️ Deprecated
- As an automation user when importing AI suggestions from external systems
- I want rqmd-ai to accept JSONL/CSV suggestion files
- So that recommendation pipelines can be processed in deterministic batches.
- Superseded by `RQMD-AUTOMATION-004` and `RQMD-AUTOMATION-015` until `rqmd-ai` defines an input schema that is materially different from the shared batch automation model.

### RQMD-AI-009: Explicit non-interactive guarantee
- **Status:** 🗑️ Deprecated
- As a CI user when running headless jobs
- I want rqmd-ai modes to avoid interactive prompts unless explicitly requested
- So that jobs never hang waiting for terminal input.
- Superseded by `RQMD-AUTOMATION-017`, which should remain the single source of truth for prompt-suppression behavior across machine-oriented CLI modes.

### RQMD-AI-010: End-to-end audit report
- **Status:** 💡 Proposed
- As a compliance-oriented user when AI modifies requirements
- I want rqmd-ai to emit a structured audit record of inputs, decisions, and outputs
- So that AI-assisted requirement changes remain traceable and reviewable.
- So that emitted audit records are sourced from the same local `rqmd-history` backend defined by `RQMD-UNDO-005` and `RQMD-UNDO-011`, rather than a parallel audit store.
