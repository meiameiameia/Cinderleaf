# Profile Model Redesign Audit

Project: `Cinderleaf / stardew-mod-manager`

Date: `2026-04-08`

## Objective

Lock the next profile-direction change before implementation so Cinderleaf moves toward a mainstream mod-manager experience instead of extending the current clone-heavy profile model.

## Repository Facts

### Current creation model

- `AppShellService.create_sandbox_mod_profile(...)` in [src/sdvmm/app/shell_service.py](C:/Users/darth/Projects/stardew-mod-manager/src/sdvmm/app/shell_service.py) currently calls `_materialize_profile_from_canonical_library(...)` and returns `linked_mod_count`.
- `AppShellService.create_real_mod_profile(...)` in [src/sdvmm/app/shell_service.py](C:/Users/darth/Projects/stardew-mod-manager/src/sdvmm/app/shell_service.py) currently calls `_materialize_real_profile_from_canonical_library(...)` and also returns `linked_mod_count`.
- The current tests explicitly lock that behavior:
  - `test_create_sandbox_mod_profile_creates_linked_profile_root_from_canonical_library(...)` in [tests/unit/test_app_shell_service.py](C:/Users/darth/Projects/stardew-mod-manager/tests/unit/test_app_shell_service.py)
  - `test_create_real_mod_profile_creates_linked_profile_root_from_canonical_library(...)` in [tests/unit/test_app_shell_service.py](C:/Users/darth/Projects/stardew-mod-manager/tests/unit/test_app_shell_service.py)

### Current toggle model

- Custom-profile toggles already add/remove junctions in the profile root instead of renaming canonical mod folders:
  - `set_sandbox_mod_enabled_state(...)`
  - `set_real_mod_enabled_state(...)`
  in [src/sdvmm/app/shell_service.py](C:/Users/darth/Projects/stardew-mod-manager/src/sdvmm/app/shell_service.py)
- `Default` is intentionally read-only for both real and sandbox profiles.
- Profile entry grouping already uses scan-entry ownership, which means grouped/container mods can be enabled or disabled at the entry level instead of only by raw folder-parent heuristics.

### Current data model

- `SandboxModProfileEntry`, `SandboxModProfile`, and `SandboxModProfileCatalog` already exist in [src/sdvmm/domain/models.py](C:/Users/darth/Projects/stardew-mod-manager/src/sdvmm/domain/models.py).
- `SandboxModProfile` already has an `entries` field, but profile creation currently does not use it as the source of truth for profile membership.
- `ModsInventory` already has both `mods` and `disabled_mods`, which means the UI and service layer already understand an enabled-vs-not-in-profile/disabled distinction.

### Current UI wording

- The UI already exposes `Not in profile` in `Library`, and the helper text already assumes a model where a mod can exist in `Default` but not in the active profile.
- Profile create/select result text in [src/sdvmm/ui/main_window.py](C:/Users/darth/Projects/stardew-mod-manager/src/sdvmm/ui/main_window.py) still advertises:
  - `Linked canonical folders`
  - `Next step: toggle mods in this profile...`
- That wording reflects the current implementation, but it is not the best long-term mainstream mental model.

## Audit Conclusion

The current profile system is functionally coherent, but it is the wrong default product model for mainstream adoption.

Its main weaknesses are:

1. New profile creation is slow on large libraries because it immediately materializes links for the whole canonical inventory.
2. The product concept is harder to explain because profile creation starts from "everything included" rather than "choose what this profile contains."
3. The visible terminal flashing was only the symptom; the deeper issue is that profile creation is doing too much work up front.
4. The current model feels like an advanced management feature instead of a simple player-facing profile system.

## Locked Target Model

The next profile model should be:

1. `Default` remains the canonical full-library view and stays read-only.
2. A new custom profile starts empty by default.
3. Enabling a mod adds that mod's top-level scan entry to the profile.
4. Disabling a mod removes that mod's top-level scan entry from the profile.
5. The profile root should only materialize links for entries that are actually enabled in that profile.
6. `Not in profile` becomes the normal inactive state for custom profiles.
7. Dependency warnings should appear when enabling a mod that requires another mod not currently enabled in that profile.

This should apply to both:

- sandbox profiles
- real profiles

The user mental model becomes:

- `Default` = everything in the canonical library
- custom profile = only the mods I turned on for this setup

## What Should Not Change

- `Default` should remain protected and read-only.
- Canonical real and sandbox mod libraries remain the source of truth for actual mod contents.
- Custom profiles still use materialized links/junctions for enabled entries.
- Grouped/container scan-entry ownership remains the right unit of membership.
- Real and sandbox profiles should continue sharing one coherent model instead of diverging unnecessarily.

## Dependency Behavior

When enabling a mod in a custom profile:

1. Resolve its required dependencies from the existing inventory/metadata model.
2. If one or more required dependencies are not enabled in the active profile:
   - surface a warning before or during the enable flow
   - keep the warning readable and player-facing
3. The first slice does not need full automatic dependency enable.

Preferred first behavior:

- warn clearly
- allow the user to decide
- optionally offer a later follow-up slice for one-click enabling required dependencies

## Recommended Implementation Order

### Slice 1

`empty custom profile creation foundation`

- change both real and sandbox custom profile creation so they create an empty profile root instead of linking the entire canonical library
- update create/select text and tests accordingly
- keep existing toggle mechanics for add/remove

### Slice 2

`profile membership truthfulness pass`

- ensure all custom-profile scans show canonical-but-not-enabled mods as `Not in profile`
- verify grouped/container entries still behave correctly
- tighten any UI text that still implies "linked clone of full library"

### Slice 3

`dependency warning on enable`

- when enabling a mod in a custom profile, warn if required dependencies are missing from that profile
- keep the first pass informational rather than automatic

## Out Of Scope For The First Slice

- profile templates
- one-click dependency auto-enable
- bulk enable/disable workflow redesign
- broad launch/recovery/archive rewiring
- cross-platform profile behavior changes

## Next Smallest Safe Increment

`empty custom profile creation foundation`

That is the smallest implementation slice that:

- fixes the slow, clone-heavy creation behavior
- aligns the product with mainstream expectations
- preserves the existing canonical-library and link-based architecture
- gives later dependency-warning work a stable profile model to build on
