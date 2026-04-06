# Engineering Roadmap

Project: `Cinderleaf / stardew-mod-manager`

Last refreshed: `2026-04-06` after update-cache work, startup auto-check, diagnostics, packages/archive improvements, cold update-check concurrency, and seven layout/build extraction passes

## Baseline

- Full unit baseline: `699 passed`
- Largest Python files:
  - `src/sdvmm/ui/main_window.py`: `13483` lines
  - `src/sdvmm/app/shell_service.py`: `10801` lines
  - `src/sdvmm/app/inventory_presenter.py`: `1305` lines
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

2. Cold update-check throughput
- `src/sdvmm/services/update_metadata.py` now deduplicates duplicate links in one run, persists fresh remote metadata between runs, and prefetches cold primary remote targets concurrently.
- The remaining user-facing speed risk is now cold-start network latency for large sets of genuinely unique providers and the lack of lightweight freshness UX, not the old fully serial loop.

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
- shared remote metadata cache per update run: done
- persisted update freshness cache: done
- startup mod update auto-check for startup-scanned contexts: done
- measured network/update instrumentation: done
- bounded cold-path primary remote prefetch concurrency: done

Next slices:

1. Cache freshness UX
- Surface when the current update state came from fresh cached metadata versus a live fetch.
- Keep the UI truthful without cluttering the inventory table.

2. Startup auto-check desktop polish
- Validate and tune startup update-check behavior on the real desktop workflow.
- Ensure status text and source switching feel calm when startup checks finish.

3. Update-check diagnostics surfacing
- Decide whether any of the diagnostics should be exposed outside logs/dev surfaces without cluttering `Library`.
- Prefer calm troubleshooting affordances over another noisy status column.

### Phase 2: Library UI Decomposition

Goal: make `Library` change-safe without weakening current behavior.

Priority extractions:

1. Inventory/update row presentation module
- Move row-state formatting, remote-link overlay behavior, and status label/tooltip mapping out of `MainWindow`.
- Status: first extraction pass done via dedicated row-application helpers inside `MainWindow`; full module split still pending.

2. Update guidance controller
- Status: first extraction pass done via dedicated guidance-state helpers and selected-row context resolution inside `MainWindow`; full controller/module split still pending.
- Keep button enabling, guidance text, and source-intent overlay logic together but out of the window class.

3. Startup workflow controller
- Status: second extraction pass done via shared startup background-batch helpers and shared startup check runner/advance helpers; full controller/module split still pending.
- Pull the startup check chain and startup auto-scan queue out of `MainWindow`.

4. Profile/action state helpers
- Status: first extraction pass done via shared action-button state resolvers for selected update and sandbox-sync actions; deeper profile-state cleanup still pending.
- Reduce profile, sandbox-sync, and selected-row action gating code inside the window class.

5. Layout/build decomposition
- Status: first extraction passes done via dedicated setup workspace surface, inventory controls tabs, and packages, compare, discovery, archive, and install workspace builders inside `MainWindow`; deeper `__init__` and `_build_layout` decomposition is still pending.
- Keep carving out coherent page/control builders instead of moving random widget lines around.

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
- Do not add broad concurrency to update checks until instrumentation shows the remaining bottleneck after cache reuse.
- Do not widen roadmap items into packaging/release changes unless a later audit shows that startup/frozen-app behavior is the real bottleneck.

## Immediate Next Safe Increment

`layout/build decomposition follow-up`

Reason:
- the update-throughput roadmap work is now materially landed
- the first setup-surface, inventory-controls, and packages/compare/discovery/archive/install workspace extraction passes are landed
- `MainWindow.__init__` and `_build_layout` remain the largest concentrated UI setup seams
- the next anti-drift win is another coherent page/control builder extraction, likely around the recovery workspace shell, before starting another product wave
