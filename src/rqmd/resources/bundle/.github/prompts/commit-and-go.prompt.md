---
description: "Work through one or more validated slices and create a clean git commit after each. A numeric argument such as /commit-and-go 10 means keep going for up to 10 committed slices."
name: "commit-and-go"
argument-hint: "Describe the task, or provide a count such as '10' to keep going and commit each validated slice."
agent: "rqmd"
---

Use the standard implementation loop, but commit after each validated slice.

- First, check whether the working tree is already dirty.
  - If the dirty changes are clearly part of the current workstream, create one clean starting-point commit before continuing so the commit-per-slice loop has a clear baseline.
  - If the changes are unrelated or ambiguous, stop and ask the user how to proceed rather than guessing.
  - If a transition commit is needed but a precise message is not obvious, use something like `checkpoint existing work before commit-and-go`.
- Clarify the smallest coherent behavior slice before editing.
- If the argument includes a positive integer `N`, treat it as a cap on how many validated slices to complete and commit before stopping.
- After each validated slice, create one clean non-amended git commit that captures that slice before continuing to the next.
- Do not sweep unrelated workspace changes into those commits.
- Keep docs and CHANGELOG aligned when the changes warrant it. Run verification before each commit.
- Keep outputs concise and make the per-slice commit progression easy to follow.
