# Cinderleaf User Manual

This guide is the detailed, player-friendly walkthrough for the current `1.4.0` release line.

If you just want the short version first, start with the main [README](../README.md).

## 1. What Cinderleaf is meant to help with

Cinderleaf is for players who want an easier, more organized mod routine on Windows, whether they only install a few favorites or like keeping different setups for different saves.

At its best, it helps you:

- look at mods before you install them
- let the watcher pick up downloaded zip files for you
- queue and install several mods together
- keep different mod sets through profiles instead of manual folder juggling
- keep backup and recovery tools nearby
- export the parts of your setup you care about before a bigger change
- compare folders without turning compare into a write action
- use sandbox workflows when you want a dedicated trial space before changing your main setup

The app can work with your real `Mods` folder, a sandbox `Mods` folder, custom profiles, backup bundles, `History`, and restore/import tools. The goal is not to make modding feel like paperwork. The goal is to make the normal install-and-play path clearer, with the safer tools nearby when you want them.

## 2. First stop: Setup

Open `Setup` first. This is where you tell Cinderleaf where everything lives.

You can configure:

- your game folder
- your real `Mods` folder
- your sandbox `Mods` folder
- your sandbox archive folder
- your real archive folder
- an optional Nexus API key

Best practice:

- keep your paths clear and consistent before you start changing things
- treat the sandbox as an optional but very useful testing area when you want to try changes before moving them into your main setup
- keep archive folders configured so rollback stays useful when you need it

`Setup` also includes update status, release-page access, backup/export tools, and restore/import tools.

## 3. Library and SMAPI

`Library` is the everyday view for your installed mods, and it is also where the main launch actions live.

Use it when you want to:

- scan what is currently installed
- browse your installed mods
- check update guidance
- look at source intent, type, and promotion context
- archive or restore the selected mod
- work with real or sandbox profiles

Some of the calmer `1.3.x` improvements live here:

- grouped multi-folder mods can stay visible as one logical entry more often
- the old `Folder` column has been replaced with a clearer `Type` column
- source state is easier to read through statuses like `Missing source`, `Needs API key`, `Built-in`, and `No tracking`
- manual-source mods can use the same update-page workflow as automatic-source mods
- checked update status now survives normal context switches more cleanly, and startup can warm update status for scanned inventories automatically

`SMAPI` is the companion tab for SMAPI-specific checks and log review.

Use it when you want to:

- open the SMAPI website
- check the installed SMAPI version
- check the latest SMAPI log
- open the latest SMAPI log file itself
- handle SMAPI-specific troubleshooting details

Use `Library` when you want the main launch actions:

- launch the game normally
- launch with SMAPI
- run a sandbox test launch

Important note:

- scanning and update guidance are read-only
- actual write actions stay explicit and live in the workflow areas where they belong

## 4. Packages

`Packages` is where downloaded archive packages come in.

You have two simple ways to use it:

- `Add package` when you just want to pick one archive and review it quickly
- the watcher when you want Cinderleaf to keep watching one or two download folders for you

Typical flow:

1. Use `Add package` for a one-off archive, or set your watched download paths and start intake watch.
2. Let Cinderleaf detect archives that are already there or appear later.
3. Filter the queue by name or status text.
4. Optionally filter the queue to watched path 1, watched path 2, or both together.
5. Use `Select all` or `Deselect all` when you want to act on only the rows currently visible under that filter.
6. Check the packages you want.
7. Choose `Compare against`.
8. Use `Open Install` to send that batch into `Install`.

If one fresh actionable watched package arrives while you are already on `Packages` and not reviewing something else, Cinderleaf can open `Install` automatically for that one obvious next step. It still does not install anything silently.

The queue status helps you understand what Cinderleaf sees, for example:

- not installed in the selected target
- same version in the selected target
- newer than the selected target

Supported package formats now include normal `.zip` files and `.rar` archives in the portable build.

`Packages` is still a review step. It does not write anything by itself.

## 5. Install

`Install` is the planning screen before any files are written.

It receives:

- the package batch you selected in `Packages`
- the destination context inherited from that earlier step

Use it to:

- confirm where the install is going
- review replace behavior
- read plan notes and install detail
- see dependency-aware batch planning results
- apply the install only after the plan looks right

One helpful part of the current workflow is batch dependency handling:

- if a needed dependency is already in the same staged batch, the plan can count it
- if that staged dependency is blocked or invalid, it does not count as safe

The plan stays read-only until Cinderleaf says it is ready to execute.

After a successful install, the Install page now leaves clearer success feedback instead of staying on stale planning text.

## 6. Profiles

Cinderleaf supports curated real and sandbox profiles.

The basic idea is:

- `Default` mirrors the main configured library
- custom profiles are smaller, curated sets
- new mods added later to the main library do not silently become enabled in older custom profiles
- if something exists in `Default` but not in the active custom profile, it shows as `not in profile`

That makes profiles useful for:

- alternate mod sets
- lighter testing setups
- preserving an older favorite combination while you try newer mods somewhere else
- keeping a cleaner test setup when you want to try changes without disturbing your main setup

## 7. Compare

`Compare` is there to help you review differences, not make changes.

Use it to:

- compare real and sandbox folders
- focus on meaningful drift instead of noise
- see cases that are only in real, only in sandbox, mismatched, or ambiguous

If you are looking for a button that makes `Compare` sync things automatically, that is not what this workspace is for. It is intentionally read-only.

## 8. History

`History` combines the old archive and recovery areas into one workspace.

It has two tabs:

- `Archived copies` for archived mod folders and restore targets
- `Install history` for recorded install/recovery history and rollback review

Use `Archived copies` when you want to:

- browse what has been archived
- inspect restore targets
- clean up older retained copies when it makes sense

Use `Install history` when you want to:

- inspect recorded install history
- review whether a recovery path looks safe
- execute recovery only when the review says it is ready

These tools are part of what makes bigger experiments less stressful.

## 9. Backup export

`Export backup` lets you choose what goes into a backup bundle instead of forcing one fixed package.

Current export choices include:

- manager state and profiles
- managed mods and config snapshots
- archives
- optional Stardew save files

Restore/import can already bring back:

- bundled mod folders
- supported mod config artifacts
- exported real and sandbox profile catalogs

Stardew save files are still different. They are exportable for backup, but today they still need manual restore steps.

In plain terms:

- export is your wider backup surface
- restore/import can already handle the guided mod/config/profile part of that surface
- save files are still the manual piece

## 10. Restore / import

Use `Inspect backup` and the related restore tools when you want to review a bundle before anything is written.

The expected posture is:

- inspect first
- plan first
- execute only after you have reviewed the result

Restore/import is archive-aware and folder-oriented. It is not meant to be a fine-grained merge tool.

Today that means:

- bundled mods can be restored
- supported mod config artifacts can be restored
- exported real and sandbox profile catalogs can be restored
- Stardew save files are still a manual restore step

## 10a. Fixing missing sources and update tracking

If a mod is missing tracking information, `Library` now gives you more guidance than the older `1.2.0` flow did.

Useful states include:

- `Missing source`
- `Needs API key`
- `Built-in`
- `No tracking`

If the app already has a strong hint, you can use:

- `Find source`
- `Suggest source`
- `Check saved source`

Important note:

- `SMAPI.*` built-ins like bundled helpers are not normal missing-source mods and should not be treated like broken tracking rows

## 11. Troubleshooting

If something goes wrong, try to collect:

- your Cinderleaf version
- your Windows version
- which workspace you were using
- the status text or error message the app showed
- the install, archive, or recovery summary if it is relevant
- whether the issue only happens in the portable packaged build or also from source

For SMAPI issues in particular:

- check the latest SMAPI log from the `SMAPI` tab
- open the log file if needed
- note whether the issue happened in real `Mods`, sandbox `Mods`, or a profile-backed launch

That makes bug reports much easier to understand and fix.

## 12. A few habits that make life easier

- use the sandbox when you want a dedicated testing space before touching live `Mods`
- keep archive folders configured
- export backups before big cleanup passes, experiments, or moving to another machine
- use profiles for curated sets instead of trying to remember manual folder edits
- treat `Compare` as a review surface
- let `Install` be your last quiet checkpoint before any write happens
- use `Add package` when you only want to inspect one archive quickly

## 13. Current boundaries

Right now, it helps to remember:

- downloads are still manual
- watcher and one-package intake can hand you off into review faster, but they still stop at review and do not install silently
- `Compare` is still read-only
- restore/import is not a full catch-all restore for every exported artifact
- there is no one-click `sync everything back to real` button
- Windows is the primary supported desktop path
