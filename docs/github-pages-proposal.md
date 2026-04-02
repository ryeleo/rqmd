# GitHub Pages Proposal

## Goal

Split the current documentation experience into two layers:

1. `README.md` as a concise marketing page and quick-start guide
2. A GitHub Pages site for the full user guide, CLI reference, AI workflow guide, and technical documentation

This keeps the repository landing page focused on adoption while giving the deeper material room to breathe.

## Why this is worth doing

Today the README is doing three jobs at once:

1. Explaining what rqmd is
2. Teaching first-time users how to get started
3. Serving as a long-form reference manual

That makes the top-level repository page dense. It is good reference material, but it is weaker as a marketing page than it could be.

The split would let the README become more persuasive and easier to skim, while GitHub Pages holds the content that benefits from more navigation, cross-linking, and room for examples.

## Proposed split

### Keep in README.md

- What rqmd is
- Why teams use it
- A short list of standout capabilities
- A few attractive rendered examples of output
- Install commands
- A short quick-start path
- A short release section pointing to the full guide
- Clear links to the full docs site

### Move or expand in GitHub Pages

- Full command guide for `rqmd`
- Full command guide for `rqmd-ai`
- Interactive workflow guide
- History, undo/redo, and recovery guide
- Config file reference
- JSON contract reference
- Roll-up and catalog customization guide
- Release guide
- Testing and CI guide
- Technical architecture and resource/template details

## Recommended site structure

Use a docs generator that publishes to GitHub Pages cleanly. The pragmatic default is MkDocs with Material for MkDocs.

Suggested navigation:

- Home
- Getting started
- Core CLI guide
- Interactive workflows
- AI workflows
- Config and customization
- JSON and automation reference
- Release and publishing
- Testing and CI
- Architecture notes

## Recommended implementation approach

### Phase 1: Prepare the content split

- Shorten `README.md` into a landing page plus quick-start guide
- Move long reference-heavy sections into dedicated docs pages under `docs/`
- Add a small "Read the full docs" section near the top of the README

### Phase 2: Publish GitHub Pages

- Add an `mkdocs.yml`
- Organize docs pages for navigation rather than one long README flow
- Publish the site through GitHub Pages from GitHub Actions
- Keep the source under version control with the rest of the repo

### Phase 3: Tune for product messaging

- Add screenshots or terminal-output cards
- Add a short comparison section: when rqmd is a better fit than ad hoc markdown status tracking
- Add a "Why this works well for humans and AI" section

## README target shape after the split

The README should ideally answer these questions in under a minute:

1. What is rqmd?
2. Why would I use it instead of plain markdown checklists?
3. What does it look like in practice?
4. How do I install it?
5. Where is the full guide?

That makes the repo landing page act more like a product page and less like a full manual.

## Success criteria

The split is working if:

- A first-time reader can understand rqmd from the README without scrolling through the full reference manual
- The docs site is easier to navigate than the current single-file flow
- Release, JSON contract, and AI workflow docs become easier to maintain because they live in purpose-built pages
- Future examples and screenshots can be added without making the GitHub repo landing page feel overwhelming

## Recommendation

Yes, this split makes sense.

The README should stay valuable as a quick-start and trust-building page, but the project has outgrown using it as the only serious end-user document. GitHub Pages is the right place for the complete user guide and technical documentation.