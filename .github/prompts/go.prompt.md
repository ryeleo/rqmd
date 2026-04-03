---
description: "Start or continue the standard rqmd implementation loop with the primary rqmd-dev agent. A numeric argument such as /go 10 means work through up to 10 validated slices before stopping."
name: "go"
argument-hint: "Describe the task, or provide a count such as '10' to keep going for up to that many validated slices."
agent: "rqmd-dev"
---

Use the standard rqmd implementation loop for this task.

- Clarify the smallest coherent behavior or requirement slice before editing.
- If the user says `next`, `go`, or otherwise asks to continue, pick the highest-priority feasible next slice instead of asking for unnecessary confirmation.
- If the argument includes a positive integer `N`, treat it as a cap on how many validated requirement slices to complete before stopping. For example, `/go 10` means keep going for up to 10 coherent validated slices.
- Keep the work requirement-first when behavior or workflow expectations change.
- Make focused edits, keep README and CHANGELOG updates aligned when needed, and run the appropriate verification before finishing.
- Do not create git commits unless the user explicitly asks for commits or invokes a commit-oriented prompt.
- Keep outputs concise and follow the standard rqmd closeout shape.
