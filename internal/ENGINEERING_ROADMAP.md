# Engineering Roadmap

Project: `Cinderleaf / stardew-mod-manager`

Last refreshed: `2026-04-05`

## Baseline

- Full unit baseline: `683 passed`
- Largest Python files:
  - `src/sdvmm/ui/main_window.py`: `12299` lines
  - `src/sdvmm/app/shell_service.py`: `9850` lines
  - `src/sdvmm/app/inventory_presenter.py`: `1124` lines
- Largest current UI orchestration hotspots:
  - `MainWindow.__init__`: `994` lines
  - `MainWindow._build_layout`: `981` lines
  - `MainWindow._refresh_selected_mod_update_guidance`: `296` lines
  - `_build_inventory_row_entries`: `173` lines
  - `MainWindow._render_inventory`: `170` lines
  - `MainWindow._apply_update_report`: `141` lines
- Largest current service hotspots:
  - `AppShellService._analyze_restore_import_execution`: `378` lines
  - `AppShellService.export_backup_bundle`: `311` lines
  - `AppShellService.migrate_cinderleaf_managed_folders`: `269` lines
  - `AppShellService.execute_sandbox_mods_promotion_preview`: `150` lines
  - `AppShellService.correlate_intake_with_updates`: `107` lines

## Audit Conclusions

The codebase is not "AI slop", but it is carrying real orchestration debt.

The main engineering risks are:

1. Oversized controller/orchestrator surfaces
- `main_window.py` is still the largest coupling point in the repo.
- `shell_service.py` still owns too many unrelated workflows.

2. Sequential update-check throughput
- `src/sdvmm/services/update_metadata.py` currently checks updates by iterating `inventory.mods` one by one.
- `_check_single_mod(...)` fetches remote metadata serially.
- There is no shared in-memory metadata cache for duplicate links in the same run.
- There is no persisted freshness cache for startup or profile switches.

3. UI state orchestration density
- `Library` state, update guidance, source-intent actions, grouped rows, and profile interactions are still heavily concentrated in `MainWindow`.
- The app is behaving better than before, but the surface remains easy to regress.

4. Large but green baseline
- A full green suite is a strength.
- The next risk is not lack of tests; it is making future changes inside very large functions/files without a stable extraction plan.

## Locked Guidance

Do not do a broad rewrite.

Prefer bounded extractions and measured behavior-preserving changes that:
- keep the full unit baseline green
- keep manual desktop validation honest for UI slices
- reduce file concentration or repeated work in one concrete place at a time

## Roadmap

### Phase 1: Update System Throughput And Persistence

Goal: make `Check for updates` fast enough and stable enough to support startup auto-checking and durable row state.

Status:
- update-report persistence by inventory context: done
- single-row patching after install instead of clearing whole report: done

Next slices:

1. Shared remote metadata cache per update run
- Deduplicate remote fetches by canonical remote link key during one `check_updates_for_inventory(...)` call.
- If multiple installed rows resolve to the same remote source, fetch once and reuse the payload.

2. Persisted update freshness cache
- Store last-known update report and a freshness timestamp per inventory context.
- Reuse fresh cached results on profile switches and scan rerenders.

3. Startup mod update auto-check
- Only after freshness caching exists.
- Run in the background for the active scanned context.
- Skip network work when cached data is still fresh enough.

4. Measured network/update instrumentation
- Add timing around:
  - update check total duration
  - number of remote links resolved
  - number of unique remote fetches
  - cache hits vs misses

### Phase 2: Library UI Decomposition

Goal: make `Library` change-safe without weakening current behavior.

Priority extractions:

1. Inventory/update row presentation module
- Move row-state formatting, remote-link overlay behavior, and status label/tooltip mapping out of `MainWindow`.

2. Update guidance controller
- Extract `_refresh_selected_mod_update_guidance(...)` into a focused helper/controller module.
- Keep button enabling, guidance text, and source-intent overlay logic together but out of the window class.

3. Startup workflow controller
- Pull the startup check chain and startup auto-scan queue out of `MainWindow`.

4. Profile/action state helpers
- Reduce profile, sandbox-sync, and selected-row action gating code inside the window class.

### Phase 3: Service Layer Decomposition

Goal: reduce `shell_service.py` from a giant workflow bucket into clearer service seams.

Priority targets:

1. Restore/import service extraction
- `_analyze_restore_import_execution(...)`
- restore/import planning helpers
- backup bundle inspection helpers

2. Backup/archive service extraction
- backup export/import orchestration
- archive restore and history helpers where practical

3. Sandbox/profile workflow extraction
- promotion preview
- profile membership/toggle helpers
- comparison/preparation helpers

4. Update/install coordination helpers
- keep narrowing install/update planning context objects and package correlation helpers

### Phase 4: Performance Guardrails

Goal: stop guessing.

Add durable checks for:
- full unit baseline timing trend
- update-check timing trend
- install-plan timing for multi-package cases
- detection of duplicate remote fetches in a single update run

## What Not To Do Yet

- Do not add broad concurrency to update checks before deduplication and cache instrumentation exist.
- Do not split `main_window.py` by random widget sections alone; extract behavior seams, not only layout code.
- Do not rewrite `shell_service.py` wholesale.
- Do not add startup mod update auto-check until cached freshness and persistence are in place.
- Do not widen roadmap items into packaging/release changes unless a later audit shows that startup/frozen-app behavior is the real bottleneck.

## Immediate Next Safe Increment

`per-run remote metadata cache for update checks`

Reason:
- it directly targets the slowest user-visible workflow
- it is measurable
- it does not require UI redesign first
- it is the cleanest prerequisite for future startup auto-checking
