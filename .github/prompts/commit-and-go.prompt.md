---
description: "Work through one or more rqmd slices and create a clean git commit after each validated slice. A numeric argument such as /commit-and-go 10 means keep going for up to 10 validated committed slices."
name: "commit-and-go"
argument-hint: "Describe the task, or provide a count such as '10' to keep going and commit each validated slice."
agent: "rqmd-dev"
---

Use the standard rqmd implementation loop for this task, but commit as you go.

- First, check whether the current working tree is already dirty. This prompt should support a seamless handoff from earlier `/go` work or manual edits.
- If the dirty changes are clearly part of the current rqmd workstream, create one clean starting-point commit before continuing so the commit-per-slice loop has a clear baseline.
- If the working tree is dirty but the changes are unrelated or ambiguous, do not guess. Either stage and commit only the clearly relevant changes, or stop and ask the user how to proceed.
- If a clean starting-point commit is needed but a precise message is not obvious, use a transition message such as `RQMD-GO-START: checkpoint existing work before commit-and-go` rather than leaving the preexisting changes uncommitted.
- Clarify the smallest coherent behavior or requirement slice before editing.
- If the argument includes a positive integer `N`, treat it as a cap on how many validated requirement slices to complete and commit before stopping.
- Keep the work requirement-first when behavior or workflow expectations change.
- After each validated slice, create one clean non-amended git commit that captures that slice before continuing to the next one.
- Do not sweep unrelated existing workspace changes into those commits. If unrelated changes conflict with the slice, stop and ask instead of guessing.
- Keep README and CHANGELOG updates aligned when needed, and run the appropriate verification before each commit.
- Keep outputs concise and make the per-slice commit progression easy to understand when reporting back.