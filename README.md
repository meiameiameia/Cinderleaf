# Cinderleaf

**Cinderleaf** is a local-first mod manager **for Stardew Valley**. It is built for players who want a smoother everyday mod routine first, with safer testing and recovery available when they need them: pick up downloads automatically, add one package quickly, review installs before writing, keep favorite profiles around, and recover cleanly if something goes sideways.

`for Stardew Valley` is a descriptive subtitle, not an official affiliation. Cinderleaf is an independent community tool and is not affiliated with or endorsed by ConcernedApe.

Current project version: **1.4.0**

Latest packaged public release: **1.3.1**

If you want the full step-by-step walkthrough, start with the [User Manual](docs/USER_GUIDE.md).

## Project snapshot

- Windows-first, local-first desktop app for Stardew Valley mod management
- built with Python, PySide6, pytest, and PyInstaller portable packaging
- centered on review-before-write installs, calmer daily-use workflows, and read-only compare
- shipped as a portable zip with GitHub Releases as the public distribution surface

## Why people use Cinderleaf

- to make mod installs feel easier and less chaotic
- to let the watcher pick up downloaded archives automatically
- to add one package quickly without setting up a whole batch first
- to review installs before writing files
- to queue and install several downloaded mods together
- to manage alternate mod profiles without losing a favorite setup
- to export backups before a cleanup, migration, or riskier change
- to compare real and sandbox folders without turning Compare into a write tool
- to keep restore, rollback, and backup tools in one easy-to-find place
- to go from a simple casual setup to a more organized, flexible routine without changing tools

## Core features

- `Library` for scanning installed mods, checking updates, handling the main launch actions, and working with your installed library
- `SMAPI` for SMAPI-specific helpers such as log checks, troubleshooting, and related actions
- `Packages` intake with watcher support, direct `Add package` intake, batch selection, and queue filtering
- `Install` planning before any write, including dependency-aware batch planning
- curated real and sandbox profiles, with clear `not in profile` behavior for mods that exist in `Default` but are not part of a custom profile yet
- read-only `Compare` for checking drift between real and sandbox mod folders
- `History` for archived copies and install-history rollback review
- backup bundle export with artifact selection, including:
  - manager state and profiles
  - managed mods and config snapshots
  - archives
  - optional Stardew save files
- restore/import support for bundled mods, mod configs, and exported profile catalogs, with save files left as a manual restore step
- optional sandbox workflows for trying changes before they reach your main setup

## New in 1.4.0

- The main workspaces are calmer and easier to scan, with cleaner hierarchy across `Library`, `Packages`, `Install`, `Setup`, and `History`.
- `Archive` and `Recovery` are now unified under `History`, keeping restore and rollback tools together without splitting the mental model across two pages.
- `Packages` is much faster in day-to-day use, with a visible one-package intake path, stronger watcher handoff, and automatic `Install` opening for a single fresh actionable download when that handoff is obvious.
- The whole app now reads more like an everyday mod manager first, instead of asking players to understand the advanced tooling before they get value from it.

For the full release history, see [CHANGELOG.md](CHANGELOG.md).

## Screenshots

These screenshots reflect the current `1.4.0` app surface.

![Cinderleaf setup workspace](media/nexus-screenshots/00-setup-workspace.png)

![Cinderleaf library workspace](media/nexus-screenshots/01-library-workspace.png)

![Cinderleaf packages workspace](media/nexus-screenshots/02-packages-workspace.png)

![Cinderleaf install workspace](media/nexus-screenshots/03-install-workspace.png)

![Cinderleaf discover workspace](media/nexus-screenshots/04-discover-workspace.png)

![Cinderleaf compare workspace](media/nexus-screenshots/05-compare-workspace.png)

![Cinderleaf history workspace](media/nexus-screenshots/06-archive-workspace.png)

## Requirements

- Windows
- Stardew Valley
- SMAPI for most modded setups

## Download the portable build

The supported public build is a Windows portable zip published on GitHub Releases.

1. Open the repository's [GitHub Releases page](https://github.com/meiameiameia/Cinderleaf/releases).
2. Download `cinderleaf-1.3.1-windows-portable.zip`.
3. Extract it to a normal folder.
4. Run `Cinderleaf.exe`.

If a checksum file is published with the release, verify `cinderleaf-1.3.1-windows-portable.zip.sha256` before announcing or mirroring the build.

Good to know:

- this is a portable folder, not an installer
- if you want to verify the download manually, compare the release zip against the published `.sha256` checksum on GitHub Releases
- Cinderleaf can tell you when a newer release exists, but it does not download or install updates for you

## A simple way to use it

1. Set your game folder, real `Mods`, and sandbox `Mods` in `Setup`.
2. Let `Packages` watch your download folders and queue the mods you want to work with.
3. Open `Install` and read the plan before you apply anything.
4. Use `Library` to keep track of what is installed and use its launch actions when you are ready to play or test.
5. Use `SMAPI` when you want log checks, troubleshooting help, or other SMAPI-specific helpers.
6. Use `Compare` when you want to see what is different between real and sandbox.
7. Use `History`, restore/import, and backup/export tools before bigger cleanups, experiments, or machine moves.

If you mainly want an easier everyday mod routine, Cinderleaf is built for that. The sandbox is there when you want a safer place to try changes first, but it is no longer the only story the app tries to tell.

## Want the full walkthrough?

The [User Manual](docs/USER_GUIDE.md) covers setup, packages, installs, profiles, backups, compare, recovery, restore/import, and troubleshooting in more detail.

## Build from source

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,build]"
.\.venv\Scripts\python.exe -m pytest tests\unit -q
.\.venv\Scripts\python.exe scripts\build_windows_portable.py
```

The build script produces:

```text
dist\cinderleaf-1.4.0-windows-portable\
dist\cinderleaf-1.4.0-windows-portable.zip
dist\cinderleaf-1.4.0-windows-portable.zip.sha256
```

## Current limitations

- downloads are still manual; the watcher can monitor folders you choose, but it does not download from mod sites for you
- Cinderleaf can auto-open `Install` for one fresh actionable watched package, but it still stops at review and does not install silently
- `Compare` is intentionally read-only; it helps you review drift, not write changes
- restore/import is archive-aware and folder-oriented; it is not a file-by-file merge tool
- exported profile catalogs can now be restored through restore/import, but Stardew save files still need manual restore steps
- there is no one-click `sync everything back to real` flow
- Windows is the primary supported desktop path today

## Feedback and issue reporting

- use GitHub Issues for bugs and feature requests
- include the Cinderleaf version, Windows version, and which workspace or workflow was involved
- if the issue involves install, archive, recovery, restore/import, or SMAPI troubleshooting, include the status text, plan summary, or error message shown by the app
- external code contributions and pull requests are not actively open right now

## License

Cinderleaf is **source-available**, not open source.

This repository is licensed under **PolyForm Noncommercial 1.0.0**. You can use, modify, and redistribute it for noncommercial purposes under the terms in [LICENSE](LICENSE).

## Project files

- [User Manual](docs/USER_GUIDE.md)
- [Changelog](CHANGELOG.md)
- [Feedback and issue notes](CONTRIBUTING.md)
- [License](LICENSE)
