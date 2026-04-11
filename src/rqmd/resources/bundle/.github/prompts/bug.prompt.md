---
description: "Quickly file a bug from the current chat context — drafts a tracked bug requirement from the conversation so a frustrated user can just type /bug and move on."
name: "bug"
argument-hint: "Optionally describe the bug, or leave blank to draft from chat context."
agent: "rqmd"
---

File a bug requirement for **your project** from the current chat context.

> **ℹ️ Info:** This prompt creates a tracked requirement in your project's `docs/requirements/` folder. To report an issue with **rqmd itself**, use `/feedback` instead.

**Goal:** Turn the problem the user has been discussing into a tracked, actionable bug requirement with minimal friction. The user is probably frustrated — be efficient, not chatty.

**Before saying anything to the user:**
1. Review the current conversation to identify the defect: what is broken, what was expected, what actually happens, and any reproduction steps already discussed.
2. Run `rqmd-ai --json` to discover the project's requirement docs directory, ID prefix, and `next_id` for the appropriate domain file. Pick the domain file that best fits the bug's subject area.
3. If the invocation argument describes the bug, use that as the primary source. Otherwise, synthesize from chat context.

**Draft the bug requirement:**
- Use the bug template shape, not user-story + Given/When/Then:
  ```
  ### PREFIX-NNN: Short description of the defect
  - **Status:** 💡 Proposed
  - **Priority:** (infer from severity — P1 for broken core flows, P2 for annoying but workable, P3 for cosmetic)
  - **Type:** bug
  - **Affects:** PREFIX-NNN (cross-reference the requirement this bug violates, if identifiable)

  **Steps to Reproduce:**
  1. ...

  **Expected:** ...

  **Actual:** ...

  **Root Cause:** *(Optional — fill in during triage or fix.)*
  ```
- Use the `next_id` from the `rqmd-ai --json` output for the chosen domain file. Never calculate IDs manually.
- Fill in as much as possible from context. Leave Root Cause as the optional placeholder unless a cause was already identified in the conversation.
- If `Affects` cannot be determined, omit the line rather than guessing.

**Write it directly:**
- Append the drafted requirement to the appropriate domain file in `docs/requirements/`. Do not ask the user for permission — just write it.
- Tell the user what you filed: the requirement ID, a one-line summary, and a link to the file.

**After filing:**
- Offer to run `rqmd --verify-summaries --non-interactive` to confirm the new requirement parses cleanly.
- If the user wants to refine the bug further, suggest `/refine PREFIX-NNN`.
- If the user wants to fix it right now, suggest `/go PREFIX-NNN`.
