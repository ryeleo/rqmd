---
description: "Refactor code, docs, or other project artifacts to improve readability, maintainability, or performance without changing external behavior."
name: "refactor"
argument-hint: "Describe what to refactor, or point at the file or area that needs attention."
agent: "rqmd"
---

Refactor the indicated code, docs, or project artifacts.

**Naming consistency**
- Audit names (variables, functions, classes, modules) for consistency and semantic clarity across the affected area.
- Prefer names drawn from established software design patterns and domain-driven design where they fit the project's language.
- Make sure the chosen names align with the project's glossary and overall domain model.

**Function decomposition**
- Split large or deeply nested functions into smaller, focused, independently testable units.
- Each extracted function should have a single clear responsibility and a name that communicates it.

**File and module organization**
- Split large files into smaller modules when distinct responsibilities are interleaved in one file.
- Each resulting file should have a clear purpose visible from its name and top-level docstring.

**Docstring and comment hygiene**
- Update docstrings to accurately describe current behavior, parameters, and return values.
- Remove stale comments that describe code that no longer exists or behavior that has changed.
- Follow a consistent docstring style and format throughout the codebase.

**Ground rules**
- Do not change external behavior — refactoring is structure-only unless the user explicitly asks for a behavior change.
- Run existing tests after each refactor step to confirm nothing broke.
- Keep changes reviewable: prefer a series of small, well-named commits over one monolithic diff.
