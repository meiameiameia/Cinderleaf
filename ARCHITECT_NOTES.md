# ARCHITECT_NOTES.md

Project name: `Cinderleaf / stardew-mod-manager`

Current stage: `READY_FOR_NEXT_INCREMENT`

Last gate decision: `PASSED - archive cleanup / retention v1 passed manual desktop validation and is ready to keep`

## Known risks

- This is a Windows desktop app, so future UI/path changes still require manual validation in addition to tests.
- Portable packaging and startup/path behavior remain high-coupling surfaces.
- There is still no dedicated architecture document beyond AGENTS/notes, so durable technical decisions must be recorded here consistently.
- Commit `135c5a72a7255c369f449e537dba64e45c2c4c02` is intentionally broad because `main_window.py`, `shell_service.py`, and GUI regression tests carried multiple coupled changes together.
- The current branch is ahead of `origin/main` by two commits and has not yet been manually validated or pushed after the commit-structuring pass.
- Archive cleanup is irreversible once confirmed; the flow is explicit, but there is no rollback for cleanup itself.
- Archive retention ordering relies on managed archive naming first and falls back to modified time for non-managed/manual folders.
- Recovery improvement is indirect: cleanup reduces archive-driven rollback clutter, but does not change install-history selectors.

## Locked decisions

- Architect / Executor / Human three-party workflow is mandatory for this repo.
- Human approval is required before every dispatch.
- `AGENTS.md` is the project-local source of truth for the workflow.
- The exact handoff format and exact gate criteria are locked and must not change without human approval.
- Stabilize before expanding is the default posture for this repo.
- The worktree split is frozen as two commits:
  - `633d7219b08d7891cf878ee64787862d44075dfe` `docs: add architect workflow scaffolding`
  - `135c5a72a7255c369f449e537dba64e45c2c4c02` `feat: add managed-folder and review context workflows`
- Archive cleanup / retention v1 is explicit/manual only; no background or automatic deletion.
- Default retention target for v1 is to keep latest `3` archived copies per mod.
- Release/version prep should continue to be handled by executor increments when the app reaches a release-worthy state; the human should not have to do version bump/build packaging manually unless explicitly choosing to.
- Completed subagent threads must be closed immediately after gating; only the current increment's active subagent may remain open.

## Open questions for human

- After manual desktop validation, should retention remain fixed at `3`, or should a later v2 expose a small user-configurable count?
