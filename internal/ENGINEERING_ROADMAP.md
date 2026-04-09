# Engineering Roadmap

Project: `Cinderleaf / stardew-mod-manager`

Last refreshed: `2026-04-09` after the `1.3.1` patch release, product-direction reset, locked profile redesign audit, and external product critique review

## Baseline

- Full unit baseline: `701 passed`
- Current release line: `1.3.1`
- Largest Python files:
  - `src/sdvmm/ui/main_window.py`: `12771` lines
  - `src/sdvmm/app/shell_service.py`: `9875` lines
  - `src/sdvmm/app/inventory_presenter.py`: `1124` lines

## Strategic Direction

Cinderleaf should now compete as a modern, everyday Stardew Valley mod manager first, with safer workflows as a built-in advantage rather than as its whole identity.

That means:

- Primary promise:
  - easiest, calmest, clearest way for normal players to install, update, and keep using mods
- Secondary differentiators:
  - review-before-write installs
  - truthful update/source guidance
  - strong archive/recovery model
  - sandbox workflows when users want them

The app should feel:

- less technical
- faster to understand
- easier to trust
- less dependent on reading dense helper text
- more aligned with normal “download mod -> review -> install -> play” expectations

## Competitive Reality

Current mainstream expectations for a Stardew mod manager are roughly:

- easy install/update flow
- profiles that feel simple
- clear update checking
- low-friction daily use

Cinderleaf already has strong differentiators in safety and recovery, but it still needs to close gaps in:

1. default-flow simplicity
2. profile mental model
3. UI density and readability
4. everyday speed and trust signals

## Audit Conclusions

The codebase is not "AI slop", but product direction can still drift unless roadmap priorities are explicit.

Main current risks:

1. Mainstream UX drift
- too much of the product story still reads like a careful advanced tool instead of a broadly welcoming everyday manager

2. Profile model mismatch
- current profile creation still materializes linked clones of the whole inventory
- this is slow on large libraries and does not match the simpler enable/disable mental model most users expect

3. UI density
- many screens are better than before, but `MainWindow` still exposes too much state and explanation at once

4. Controller concentration
- `main_window.py` and `shell_service.py` remain the biggest long-term change-risk surfaces

## External Audit Synthesis

An external product critique on `2026-04-09` largely confirmed the current strategic direction.

Confirmed strengths:

- Cinderleaf's strongest market differentiator is still the calm, reversible, review-before-write workflow.
- Documentation quality is already a real product advantage and should stay that way.
- Update-truthfulness, recovery, backup export, and grouped-mod handling are all meaningful strengths worth preserving.

Confirmed weaknesses:

1. UI still feels slightly more like a careful dev tool than a mainstream everyday manager.
2. Screen chrome and helper density still compete too much with the actual mod-list/task surface.
3. Trust friction is still real on Windows because unsigned-portable distribution creates first-run caution.
4. Visibility/distribution is still much weaker than product quality.

Adopted guidance:

- keep pushing toward a calmer, lower-reading, mod-list-first default UI
- continue trimming chrome and secondary text where it is not helping the immediate task
- keep positioning Cinderleaf as a mainstream everyday manager with safety as the differentiator, not as an expert-only tool

Not adopted as near-term engineering priorities:

- broad cross-platform expansion
- feature-for-feature cloning of Stardrop
- license/contribution-policy changes as a substitute for product improvement

## Locked Guidance

Do not try to compete by cloning Stardrop feature-for-feature.

Compete by being:

- clearer on Windows
- safer during installs/updates
- calmer in everyday use
- more truthful when something is ambiguous or risky

Do not do a broad rewrite.

Prefer bounded changes that:

- improve the default player experience
- keep the full unit baseline green
- require manual desktop validation for UI/product-flow slices
- reduce controller density one concrete seam at a time

## Roadmap

### Phase 1: Mainstream Default Workflow

Goal: make the normal player path feel obvious and low-friction.

Priority slices:

1. Primary happy-path audit
- Re-audit the user journey from:
  - first setup
  - watcher/package intake
  - install review
  - launch
  - update check
- Trim or hide low-value technical phrasing from the default path.

2. Install/update CTA hierarchy
- Keep the main action of each workspace visually obvious.
- Reduce secondary-action competition in the `Library`, `Packages`, and `Install` surfaces.

3. Calmer status language
- Prefer player-facing status copy over tool-facing diagnostics in the default view.
- Keep detailed troubleshooting available, but not dominant.

4. Chrome compression
- Reduce persistent header/footer and surrounding frame weight where they shrink the working surface.
- Make the table/list area feel like the main event, especially in `Library`, `Packages`, and `Install`.

### Phase 2: Profile Model Redesign

Goal: make profiles behave the way mainstream users expect.

Target model:

- a new profile starts empty, or from an explicit template chosen by the user
- enabling a mod adds it to that profile
- disabling a mod removes it from that profile
- dependency warnings appear when enabling a mod that needs another mod not present in the profile

Why this is next:

- it directly addresses the current slow, noisy, clone-heavy profile creation behavior
- it makes profiles easier to explain
- it aligns Cinderleaf with mainstream mod-manager mental models

Bounded implementation order:

1. audit and lock the desired data/model behavior
2. redesign profile creation UI and service semantics
3. restore grouped multi-folder profile membership behavior so grouped mods can be added or removed as one logical entry
4. add dependency-warning behavior on enable
5. then revisit profile-related wording and docs

Audit status:

- the profile redesign audit is now locked in [internal/PROFILE_MODEL_REDESIGN_AUDIT.md](C:/Users/darth/Projects/stardew-mod-manager/internal/PROFILE_MODEL_REDESIGN_AUDIT.md)
- the next step is implementation, not more product-direction drift

### Phase 3: Update And Install Experience

Goal: make updates and installs feel fast, truthful, and stable.

Already landed:

- update status persistence by inventory context
- faster remote metadata reuse and cold-target prefetching
- startup auto-check for warmed inventories
- better row patching after install/update-related actions

Next slices:

1. cache freshness UX
- show when a result is fresh enough to trust without cluttering `Library`

2. clearer row-level update truth
- keep strengthening cases where remote-page truth, package-manifest truth, and installed-manifest truth do not fully align

3. guided source/update flows
- continue reducing friction for manual-source and hinted-source update paths

### Phase 4: UI Calmness And Density Reduction

Goal: make the app feel modern, approachable, and lower-reading.

Priority targets:

1. `Library` right-rail simplification
- keep the selected-row actions clear without stacking too many panels and helper paragraphs

2. setup/onboarding polish
- keep setup readable for normal players
- make archive, restore/import, and advanced options feel available but not overwhelming

3. global typography and spacing refinement
- continue the `1.3.1` direction carefully
- prefer clarity, stronger hierarchy, and calmer defaults over dramatic visual experimentation

4. workspace shell simplification
- continue simplifying workspace shells so the mod/task content wins over surrounding UI furniture
- favor compact context cards and lighter always-visible framing
- likely early candidates:
  - collapsible top session/status strip
  - optional icon-only workspace rail
  - a less always-open details panel in `Library`

### Phase 5: Maintainability And Decomposition

Goal: keep the codebase change-safe while product work continues.

Priority targets:

1. `MainWindow` decomposition
- continue bounded extraction of:
  - layout/build seams
  - update guidance/state seams
  - selected-row action/state seams

2. `AppShellService` decomposition
- keep narrowing large workflow buckets, especially:
  - restore/import
  - backup/archive
  - profile workflows

3. performance guardrails
- keep timing and duplication checks around:
  - update checks
  - install planning
  - large-library workflows

## What Not To Do Yet

- Do not widen into cross-platform positioning work yet.
- Do not attempt a broad visual redesign before the profile and happy-path flows are calmer.
- Do not let advanced sandbox/recovery workflows define the first-run experience.
- Do not rewrite `main_window.py` or `shell_service.py` wholesale.
- Do not ship major new feature waves without checking them against this roadmap first.
- Do not treat distribution, trust, or community growth problems as a reason to dilute the product direction into generic feature cloning.

## Non-Code Tracks To Remember

These matter, but they are not the next engineering slice:

1. Distribution and trust
- code signing or other Windows trust improvements remain valuable later
- checksum guidance should stay simple and user-facing

2. Visibility
- refreshed screenshots, demo material, Nexus polish, and community presence still matter materially for adoption

3. Platform reach
- cross-platform support is strategically interesting, but should follow a stronger mainstream Windows experience rather than precede it

## Immediate Next Safe Increment

`grouped multi-folder profile membership in custom profiles`

Reason:

- the empty-profile foundation and membership-truthfulness pass are now landed
- the next product bug is that grouped multi-folder mods stop behaving like one logical entry inside custom profiles
- this directly hurts the mainstream profile workflow because users have to toggle grouped mods one folder at a time
- it should land before dependency warnings or chrome compression because it is a correctness and usability gap in the core profile model
