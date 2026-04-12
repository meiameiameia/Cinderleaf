# Cinderleaf User Guide

This is the easy-to-read guide for the current `1.4.0` release line.

If you want the short version first, read the main [README](../README.md).

## 1. What Cinderleaf is for

Cinderleaf is for Stardew Valley players who want modding to feel more organized without turning it into a chore.

It helps you:

- see what is installed
- catch new mod archives in one place
- review installs before changing files
- catch missing required dependencies during install planning
- keep different profiles for different saves or playstyles
- use a sandbox when you want a safer test setup
- recover from bad changes more easily

You do not need to use every feature to get value from it.

If all you want is:

- add a mod
- check what is installed
- update things
- launch the game

Cinderleaf is meant to help with that too.

## 2. Your simplest first setup

Open `Setup` first.

The main folders to set are:

- your game folder
- your real `Mods` folder
- your sandbox `Mods` folder

The sandbox folder is optional in spirit, but recommended if you like testing things before they touch your main setup.

Once those are set, you are ready to use the normal flow.

## 3. The normal everyday flow

The easiest way to think about the app is:

1. bring mod archives into `Packages`
2. review them in `Install`
3. use `Library` to manage what is installed and launch the game

Everything else supports that routine.

## 4. Packages

`Packages` is where mod archives come in.

You can use it in two ways:

- click `Add package` when you want to pick one archive quickly
- use the watcher when you want Cinderleaf to keep checking one or two download folders for you

Typical flow:

1. Open `Packages`.
2. Either click `Add package` or start the intake watcher.
3. Let the app detect your archive files.
4. Check the package rows you want.
5. Choose what to compare against.
6. Open `Install`.

Important:

- `Packages` does not install anything by itself
- it is still a review step
- the app may open `Install` automatically for one obvious watched package, but it still stops at review

## 5. Install

`Install` is the last check before anything is written.

This is where you:

- confirm the destination
- review whether something will replace an existing target
- see dependency warnings before the write step
- read the summary
- apply the install only when it looks right

That is one of Cinderleaf’s main safety ideas:

- get to review faster
- still keep the write step explicit

Dependency handling matters here too:

- if a required dependency is missing, the plan can warn or block before install happens
- if a dependency is already included in the same staged install batch, Cinderleaf can count that instead of treating it like missing
- remote requirement hints are not the same thing as the blocking local dependency check

## 6. Library

`Library` is the main everyday management screen.

Use it to:

- scan installed mods
- check updates
- open source pages
- launch the game
- launch with SMAPI
- launch a sandbox test
- work with profiles

If you spend most of your time in one workspace, it will probably be `Library`.

## 7. SMAPI

`SMAPI` is the companion area for SMAPI-specific tasks.

Use it when you want to:

- check your SMAPI version
- look at the latest SMAPI log
- open the SMAPI website
- get troubleshooting help for modded launches

## 8. Profiles

Profiles let you keep different mod sets without manually moving folders around.

The simple way to think about them:

- `Default` mirrors the main library
- custom profiles let you keep smaller or different selections

Profile dependency handling is built in too:

- if you enable a mod in a custom profile and its required dependency is already installed, Cinderleaf can add that dependency to the profile automatically
- if the dependency is not installed at all, Cinderleaf can warn you instead of silently leaving the profile in a confusing state

This is useful if you want:

- one setup for a long-running save
- another for testing
- another for a themed playthrough

## 9. Sandbox

The sandbox is a separate `Mods` setup.

That means:

- your real `Mods` folder stays your main setup
- the sandbox gives you another place to try things first

If a test goes well, you can keep moving from there.
If it goes badly, your real mod setup was not the place where you experimented.

This helps most with mod setup safety.

It does **not** mean Cinderleaf is secretly creating a full isolated save-management system for you. If you are testing something that could affect save data directly, using a copied save is still the careful move.

## 10. Compare

`Compare` is read-only.

It is there so you can check what is different between your real setup and your sandbox setup.

Use it when you want to answer questions like:

- what exists only in real?
- what exists only in sandbox?
- what versions do not match?

It is a review tool, not a write tool.

## 11. History

`History` is where older state and rollback information now live.

It has two tabs:

- `Archived copies`
- `Install history`

### Archived copies

Use this when you want to:

- browse archived mod copies
- restore an archived copy
- delete an archived copy
- clean up older retained copies

### Install history

Use this when you want to:

- inspect recorded install history
- review rollback information
- apply recovery only after you have reviewed it

The point is to keep restore and rollback tools together in one place instead of splitting them across two different workspace names.

## 12. Backup and restore

Cinderleaf can export backup bundles that include things like:

- manager state and profiles
- managed mods and config snapshots
- archives
- optional Stardew save files

This is useful before:

- bigger cleanup passes
- machine moves
- major mod changes
- riskier experiments

Restore/import can already handle the guided mod/config/profile side of those bundles.

Save files are still different:

- they can be included in export
- save restore is still manual

## 13. Discover

`Discover` helps you look up mods by name, author, or UniqueID and open their pages.

It is meant to help with:

- finding a mod page
- checking source information
- reconnecting tracking info

It does not install mods by itself.

## 14. If something goes wrong

If you want to report a bug, it helps to include:

- your Cinderleaf version
- your Windows version
- which workspace you were using
- the status text or error message you saw
- whether it only happens in the portable packaged build or also from source

For SMAPI issues, it also helps to mention whether it happened in:

- real `Mods`
- sandbox `Mods`
- a specific profile

## 15. Good habits

These habits make Cinderleaf easier to use:

- use `Add package` when you only want to handle one archive quickly
- use the watcher when you download several mods in a row
- let `Install` be your final quiet checkpoint before a write
- use profiles instead of manual folder juggling
- use the sandbox when you want a safer place to experiment
- use `History` when you need restore or rollback help

## 16. Current limits

Right now, it helps to remember:

- downloads are still manual
- `Compare` is still read-only
- Cinderleaf helps you get to review faster, but it still does not install mods silently
- save restore is still manual
- Windows is the main supported desktop path
