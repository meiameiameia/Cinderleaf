# ARCHITECT_CHECKLIST.md

Use this as a short operational checklist. `AGENTS.md` remains the source of truth if there is any mismatch.

## Session start

- Read `AGENTS.md` before doing implementation or dispatch work.
- Confirm whether this turn is:
  - repo inspection / gate review
  - local tiny docs/process maintenance
  - local tiny hotfix
  - normal bounded implementation slice
- Default to dispatch for normal bounded implementation slices.
- If executing locally, state why dispatch is not the safer default.
- Confirm there is at most one active subagent for the current increment.

## Before dispatch

- Inspect the relevant repo files first.
- Lock scope narrowly.
- Name the required validation shape:
  - unit-only
  - manual UI validation
  - packaging/build validation
  - CI/workflow validation
  - documentation-only validation
- Emit the exact `Pre-Dispatch` block.
- Emit the exact `Dispatch` block.

## Before gate

- Review the actual diff, not only the handoff prose.
- Verify validation claims against commands, file read-backs, or manual notes.
- State any remaining manual-validation gap honestly.
- Emit the exact `Gate Decision` block.

## After gate

- Close the subagent immediately if one was used.
- If the slice changed architecture, routing assumptions, or release mechanics, update `ARCHITECT_NOTES.md`.
- If the bounded slice is validated and required manual checks are done, commit it promptly instead of letting the worktree sprawl.
