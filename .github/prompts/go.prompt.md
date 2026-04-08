---
description: "Start or continue the implementation loop. A numeric argument such as /go 10 means work through up to 10 validated slices before stopping."
name: "go"
argument-hint: "Describe the task, or provide a count such as '10' to keep going for up to that many validated slices."
agent: "rqmd-dev"
---

Use the standard implementation loop for this task.

- Clarify the smallest coherent behavior slice before editing. Do not ask unnecessary clarifying questions when the intent is clear.
- If the user says `next`, `go`, or otherwise asks to continue, pick the highest-priority feasible next slice instead of asking for confirmation.
- If the argument includes a positive integer `N`, treat it as a cap on how many validated slices to complete before stopping. For example, `/go 10` means keep going for up to 10 coherent validated slices.
- Keep the work requirement-first when tracked requirements exist.
- Make focused edits with minimal behavior drift. Keep docs, README, and CHANGELOG aligned when the changes warrant it.
- Run the appropriate verification (tests, lints, smoke checks) before finishing each slice.
- Do not create git commits unless the user explicitly asks for commits or invokes `/commit` or `/commit-and-go`.
- Keep outputs concise. Follow the standard closeout shape when finishing a batch.
