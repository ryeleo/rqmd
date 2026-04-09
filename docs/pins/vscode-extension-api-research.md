# VS Code Extension Contribution Points for Copilot Chat Files

> **Date:** 2026-04-08 — researched against VS Code 1.115+ / Copilot Chat 0.43.0

## TL;DR

VS Code **does** support extensions contributing `.prompt.md`, `SKILL.md`, `.agent.md`, and `.instructions.md` files via declarative `package.json` contribution points. The mechanism is real, actively used, and handled by VS Code core — not the Copilot extension. **No proposed API gating was found on the declarative contribution points**, even though the associated TypeScript API (`vscode.chat.*`) is still a proposed API.

## Contribution Points

Four declarative contribution points exist in `package.json`:

| Contribution Point | File Type | Example |
|---|---|---|
| `chatPromptFiles` | `.prompt.md` (slash commands) | `{"path": "./prompts/go.prompt.md"}` |
| `chatSkills` | `SKILL.md` (domain skills) | `{"path": "./skills/my-skill/SKILL.md"}` |
| `chatAgents` | `.agent.md` (agent definitions) | `{"path": "./agents/dev.agent.md"}` |
| `chatInstructions` | `.instructions.md` (scoped instructions) | `{"path": "./instructions/style.instructions.md"}` |

### Entry Schema

Each entry accepts:
- **`path`** (required): Relative path from extension root to the file
- **`when`** (optional): Context expression to conditionally enable (e.g., `"chatSessionType == local"`)
- **`name`** (deprecated): Use YAML frontmatter in the file instead
- **`description`** (deprecated): Use YAML frontmatter in the file instead

### copilot-instructions.md

Not a contribution point. `copilot-instructions.md` is discovered by workspace path (`.github/copilot-instructions.md`). Extensions cannot contribute a `copilot-instructions.md` file through the contribution mechanism. Per-project instructions overrides would remain as workspace files.

## Proposed API vs Declarative Point

The `chatPromptFiles` proposed API (version 1) defines **two things**:

1. **Declarative contribution points** (`contributes.chatPromptFiles` etc. in `package.json`)  
   - Registered via `registerExtensionPoint()` in VS Code core  
   - **No proposal validation found in the handler** — any extension's entries are processed  
   - 55 total `registerExtensionPoint` calls in VS Code; **none** gate on proposed APIs

2. **TypeScript runtime API** (`vscode.chat.registerPromptFileProvider` etc.)  
   - Gated by `enabledApiProposals: ["chatPromptFiles"]`  
   - Only works for allowlisted publishers or dev-mode extensions

### Publisher Allowlist (for TypeScript API only)

Only two publishers are currently allowlisted for `chatPromptFiles`:
- `GitHub.copilot-chat`
- `ms-dotnettools.vscode-dotnet-modernize`

This allowlist restricts the **TypeScript API**, not the declarative contribution points.

## Resource Source Model

The API models four resource sources via `ChatResourceSource`:
```typescript
type ChatResourceSource = 'local' | 'user' | 'extension' | 'plugin';
```

Every resource type (`ChatCustomAgent`, `ChatInstruction`, `ChatSkill`, `ChatSlashCommand`) includes:
- `source: ChatResourceSource` — where it was loaded from
- `extensionId?: string` — the contributing extension ID when `source === 'extension'`

This means VS Code explicitly models and tracks extension-contributed Copilot files as a first-class concept.

## How Copilot Chat Uses This

Copilot Chat (0.43.0) contributes via its own `package.json`:

```json
"contributes": {
  "chatPromptFiles": [
    {"path": "./assets/prompts/plan.prompt.md", "when": "chatSessionType == local"},
    {"path": "./assets/prompts/init.prompt.md", "when": "chatSessionType == local"},
    {"path": "./assets/prompts/create-prompt.prompt.md", "when": "chatSessionType == local"},
    ...
  ],
  "chatSkills": [
    {"path": "./assets/prompts/skills/agent-customization/SKILL.md", "when": "chatSessionType == local || chatSessionType == copilotcli"},
    {"path": "./assets/prompts/skills/troubleshoot/SKILL.md", "when": "chatSessionType == local || chatSessionType == copilotcli"},
    ...
  ]
}
```

These files live inside the extension's install directory and are discovered by VS Code core via the `chatPromptFilesExtensionPointHandler` workbench contribution.

## What This Means for rqmd (RQMD-PACKAGING-013)

### Likely works (needs empirical validation)

A `ryeleo.rqmd` VS Code extension on the Marketplace with:
```json
{
  "contributes": {
    "chatPromptFiles": [
      {"path": "./prompts/go.prompt.md"},
      {"path": "./prompts/bug.prompt.md"},
      ...
    ],
    "chatSkills": [
      {"path": "./skills/rqmd-implement/SKILL.md"},
      ...
    ],
    "chatAgents": [
      {"path": "./agents/rqmd-dev.agent.md"},
      ...
    ]
  }
}
```

...should have its files discovered by VS Code core and available in Copilot Chat, because:
1. The handler processes entries from all installed extensions
2. No proposed API check gates the declarative contribution point
3. Path resolution is relative to the extension's install directory
4. Security: paths must stay within the extension boundary (enforced)

### Unknown: `copilot-instructions.md`

There is no contribution point for `copilot-instructions.md`. Extensions cannot inject project-level instructions. The rqmd extension would need to either:
- Use `chatInstructions` (`.instructions.md` files with `applyTo` patterns) as an alternative
- Leave `copilot-instructions.md` as a workspace-level file for per-project customization

### Recommended validation

Build a minimal test extension with one `.prompt.md` entry in `chatPromptFiles`, install it locally (VSIX or dev mode), and check:
1. Does the `/` slash command list show the extension's prompt?
2. Does a `SKILL.md` entry appear in agent skill discovery?
3. Does an `.agent.md` entry appear in agent mode selection?

Test extension scaffold is at `tmp/rqmd-vscode-test/`.
