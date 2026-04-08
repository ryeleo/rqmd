# Brainstorm

## Prompts

/feedback: Send feedback aimed at improving rqmd.
- First, send some telemetry whenever this is invoked
- Then, work with the user to craft the telemetry payload to be as useful as possible for future development/improvement of rqmd. Send updates to the telemetry server as the payload evolves based on user feedback and input.
- Developer commentary: This will probably become one of my (rqmd's primary developer's) primary development workflows to make changes to rqmd. I will go use rqmd in many other projects with a mind on making improvements to rqmd itself, and will use "/feedback" to start actaully accumulating actionable feedback and telemetry on how rqmd is being used, where it is falling short, and what improvements would be most valuable to users in the future. This will help me prioritize my work on rqmd and make sure I am building the most useful features and improvements for users based on real-world usage and feedback.
- Consider submitting gh issue to ryeleo/rqmd repo direcly if there is an actual issue noticed during this feedback session (and the user has gh cli installed and authenticated)

Promoted into tracked requirements: `RQMD-AI-053` (/feedback prompt), `RQMD-AI-054` (/rqmd-feedback skill), `RQMD-AI-055` (GitHub issue creation from feedback), `RQMD-TELEMETRY-015` (feedback event type).

---

/refactor: Refactor code, docs, or other project artifacts to improve readability, maintainability, or performance. 
- Naming: Consistent naming of all domain logic -- work with the developer on making names consistent and semantically meaninful throughout their code base. Use names from Software Design Patterns and Domain-Driven Design where possible, and make sure that the names chosen align with the overall goals and language of the project.
- Splitting large functions into smaller more focused more testable functions.
- Splitting large files into smaller more focused files that each have a clear purpose and responsibility.
- Ensuring docstrings are up to date and accurately describe the behavior of the code, and that they follow a consistent style and format throughout the codebase.


/polish-docs: Extra Note, we should make sure all docstrings are up to date and accurate when doing docs polish in general. Hate it when project docs and docstrings get out of sync!

---

/commit: Commit the current work with a nice git commit message to make it easier to keep track of changes and have a clear history of what was done and why. This is especially important when working with AI agents, as it helps maintain a clear record of the decisions made and the changes implemented based on those decisions. Similar to rqmd-changelog skill, make sure that the human inputs and decisions are clearly reflected in the commit messages, while the AI work is given a custom H1 heading to make it clear what was done by AI vs humans in the commit history. This way we can maintain a clear narrative in our commit history that highlights the human-driven decisions and changes, while still acknowledging the important AI-driven work that supports those changes. Having the AI Agent specify its own model and version in the commit message can also help with tracking how our AI capabilities evolve over time and provide context for the reliability of the changes made.
/go: Continue with what you were currently doing.
/next: Work with the user on picking what to work on next.
/refine: Work with the user on refining requirements. (This can easily become brainstorming if the user isn't sure what they want yet, or it can be more focused on fixing-up existing requirements if they have a specific requirement in mind that they want to refine.)
/brainstorm: Think broadly and creatively about the project, requirements, implementation, or any other aspect of the work. This is a more open-ended prompt that encourages exploration and idea generation. Regularly suggest that new requirements could be drafted/created (and existing ones updated to reflect the new brainstorm). When in brainstorm mode, offer loose titles to requirements only, not full requirements.


## Performance optimizing for rqmd-ai speed

Figure out how to make rqmd commands used by AI MUCH faster so the feedback loop is much tighter and we can do more iterative prompting and less "put in a big prompt, wait a long time, get a big response" cycles.

Promoted into tracked requirements: `RQMD-CORE-037` (lazy imports), `RQMD-CORE-038` (filesystem cache), `RQMD-CORE-039` (non-interactive latency budget), `RQMD-CORE-040` (native Rust/C acceleration roadmap), and `RQMD-AUTOMATION-038` (multi-query batch mode).

## Telemetry Local Dev

Back to Telemetry Local Dev -- I should have said that I want to be able to use local tools to access the REMOTE servers -- so make sure there is a docker compose solution that runs just the admin tools and hopefully is even autoconfigured to reach 

Oh yeah, set me up so that I can have easy access to the backend of the telemetry services to - I am not very good at DB work and being able to pull up a basic spreadsheet view of any DB table is very helpful for me! Maybe run some basic docker containers locally that give me access? Maybe just recommend VS Code extensions?


## Telemetry Feedback Loop

When I come back to this project to do any development, I want to have an easy way to have AI take all the input. 

Eventually, I would like a weekly GitHub Action job that runs this script, and makes a PR if there is worthwhile changes to be made automatically.


## Make Telemetry opt-out

Telemetry on by default, but user can opt out.



## rqmd ai agent should be VERY well versed in rqmd

The entire CLI, > rqmd-ai install
rqmd-ai mode: install-agent-bundle
read-only: no
> rqmd-ai install --overwrite-existing
rqmd-ai mode: install-agent-bundle
read-only: no

## Agent skill: allow commands for AI agents

## Interview Questions

- Should we use simple or expanded statuses?
- Should we use rqmd-agents and rqmd-skills? Should we overwrite/write you a  copilot-instructions.md per rqmd recommendations?
- 

## "🤖 AI Verified" status

This is a proposed new status label to indicate that a requirement has been verified by an AI agent rather than a living being. It could be used in cases where the requirement has been implemented and the implementation has been validated through automated tests or other machine-driven verification methods, but has not yet been reviewed and approved by a living being.

Is there much value here? It isn't like we want to have to test EVERYTHING that the AI can test for us, right? But, for postarity it is probably a good idea to be able to distinguish between things that have been verified by a human and things that have only been verified by an AI, especially if we want to eventually have some kind of "AI-verified" badge or filter in the interactive UI.

Also, we should probably pin which AI agent model was used for the verification, and maybe even the date it was verified, so we can track how our AI verification capabilities evolve over time and have more context for the reliability of the verification.

## New rqmd-* skill: rqmd-pin

Use `rqmd-pin` to create a pinned note that captures important context, decisions, or other information that you want to keep easily accessible during your work with rqmd. Pinned notes can be used to:
- Keep track of key decisions or insights that come up during brainstorming or implementation.
- Save important context that you want to refer back to later without having to search through chat history or documentation.
- Create a quick reference for yourself or others on the team about specific topics related to the project.

Work with the user to decide where their pinned notes should be stored (e.g., a specific markdown file, a dedicated section in the README, or even a folder like `docs/pins/` with individual pinned ideas per file!) and how they want to format the pinned information for easy readability and reference.

Promoted into tracked AI workflow requirement `RQMD-AI-042`.

## New rqmd-* skill: rqmd-changelog

Use ["keep a changelog"](https://keepachangelog.com/en/1.1.0/) principles to maintain a clear and user-focused `CHANGELOG.md` that highlights the most important changes driven by human decisions and key functional updates, while still acknowledging the AI-driven work that supports those changes.

Right now, the changelogs we are creating are not great...

They should absolutely be focused on the line items that were driven by:
1. (living being) requests given to AI by a living being, or
2. (living being) changes/additions/removals made directly by a living being in the code or docs and not by AI, or
3. (key info) changes/additions/removals that are essential to how the project functions for end users.

The other things that AI had to do to make those requests actually happen should be shown, but under a nested (H4? I think?) heading like "AI Development" or something.

This way we can keep the human-driven narrative clear and focused, while still acknowledging the important AI-driven work that went into making those changes possible.

Promoted into tracked AI workflow requirement `RQMD-AI-039`.

## Discovery Mode

Explore vs Discovery... What is the difference...

Exploring is open ended, breadth focused, and doesn't have an end result required. It can be what it can be.

Discovery is more focused on finding specific information or insights that can help drive key decisions for the project. It helps the user make decisions.

Solving is more focused on a specific question or problem that might/could have a solution.



## Consistent AI Experience with rqmd-agents

We want rqmd agents to behave similarly in each project they are added to. They should provide similar outputs and follow similar workflows across projects, even if the underlying requirement content and priorities differ. This consistency helps users build trust and familiarity with the AI features, and it allows us to create reusable documentation, training materials, and best practices that apply broadly.

### AI output should use "info" "note" and "warning" block quotes like in our README.md

### AI output should use consistent emoji and status formatting for proposed/implemented/verified/blocked/deprecated items, matching the README guidance

Promoted into tracked AI workflow requirement `RQMD-AI-041`.



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
- Windows-safe `rqmd-ai --json` capture guidance (foreground + stdout-only parsing + separate stderr): `RQMD-AI-012`.
- Init status-scheme selection (`canonical`/`lean`/`delivery`) plus copy-from-existing-project path: `RQMD-AI-029`.
- Combinable filter semantics and `--update-flagged`: `RQMD-AUTOMATION-025`, `RQMD-AUTOMATION-032`, `RQMD-AUTOMATION-034`, and `RQMD-AUTOMATION-035`.
- Screen-write vs scrolling UI: `RQMD-UI-001` and `RQMD-UI-003`.
- Undo/redo with persistent history: `RQMD-UNDO-001` and `RQMD-UNDO-002`.
- `ReqMD` rename exploration: `RQMD-PACKAGING-012`.
- JSON schema versioning: `RQMD-AUTOMATION-033`.

## Newly promoted from this pass

- `RQMD-AI-036`: long-running priority-first development agent (`rqmd-dev-longrunning`).
- `RQMD-AI-037`: easy-first low-hanging-fruit development agent (`rqmd-dev-easy`).
- `RQMD-AI-039`: authored changelog-maintenance skill (`rqmd-changelog`).
- `RQMD-AI-041`: consistent cross-project AI workflow experience.
- `RQMD-AI-042`: pinned context and decision notes workflow (`rqmd-pin`).
- `RQMD-CORE-033`: versioned requirement markdown schema and migration path.
- `RQMD-CORE-034`: guided duplicate-ID repair workflow.
- `RQMD-SORTING-016`: positional `rqmd ranked` target for backlog grooming.
- `RQMD-INTERACTIVE-032`: grapheme-safe menu alignment for emoji-rich labels like `⚠️ Janky`.
- `RQMD-CORE-037`: lazy import strategy for non-interactive codepaths.
- `RQMD-CORE-038`: filesystem-cached parsed catalog for repeated invocations.
- `RQMD-CORE-039`: non-interactive latency budget and CI gate.
- `RQMD-CORE-040`: native Rust/C acceleration for parse and index hot paths.
- `RQMD-AUTOMATION-038`: multi-query batch mode for rqmd-ai.

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

The `Speed Shooting VR` status issue is not a generic parser incompatibility. It only fails when rqmd is pointed at `test-corpus/SSVR/requirements` while the project root stays at this repository, which means the corpus-local `rqmd.yml` is not loaded. If we want cross-root `--docs-dir` flows to auto-discover a neighboring config, that is a separate future requirement.

## Still worth triaging later

- Add even more agent-opinionated interview/prompt payload hints, for example `render_as_checkbox_prompt`, `do_not_summarize_after_each_answer`, or similar explicit downstream UX knobs.
- Improve terminal markdown rendering beyond the current lightweight bold/headings support.
- Consider explicit `Ctrl+Z` / `Ctrl+Y` bindings on top of the existing undo/redo feature set.
- Decide whether README generation should eventually become a stronger "tool-owned index" policy rather than marker-bounded sync.
- Explore whether cross-root config discovery should follow `--docs-dir` targets when users intentionally point rqmd at another repository's requirement catalog.
- Revisit native acceleration later if the current Python implementation becomes a real bottleneck despite the existing optional speedups path. — Promoted into `RQMD-CORE-040`.

