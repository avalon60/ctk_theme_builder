# CTkThemeBuilder Wheel/PyPI Deployment Migration Plan

## Assessment

The repository is not wheel-ready in its current form. It is still built around an unpacked, writable application tree plus shell/batch launchers and an external installer.

High-confidence findings:

- Packaging is explicitly disabled for Poetry. [pyproject.toml](/home/clive/PycharmProjects/ctk_theme_builder/pyproject.toml):39
- There are no wheel-style entry points; launch is still via repo-relative `.sh`/`.bat` wrappers that assume `.venv`, mutate `PYTHONPATH`, and dispatch to the controller module under `ctk_tb`. [ctk_theme_builder.sh](/home/clive/PycharmProjects/ctk_theme_builder/ctk_theme_builder.sh):11 [ctk_theme_builder.sh](/home/clive/PycharmProjects/ctk_theme_builder/ctk_theme_builder.sh):14 [ctk_theme_builder.sh](/home/clive/PycharmProjects/ctk_theme_builder/ctk_theme_builder.sh):53 [ctk_tb/controller/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/ctk_tb/controller/ctk_theme_builder.py):17
- Core runtime paths are derived from the install/repo root and point at writable locations inside it: `assets/data`, `assets/palettes`, `assets/etc`, `tmp`. [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):25
- Preferences and runtime state are stored in a SQLite DB under the install tree, and many imports assume that DB already exists. [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):41 [model/preferences.py](/home/clive/PycharmProjects/ctk_theme_builder/model/preferences.py):23 [utils/loggerutl.py](/home/clive/PycharmProjects/ctk_theme_builder/utils/loggerutl.py):57
- The current first-run/bootstrap path lives in `theme_builder_setup.py`, not in the application itself. It creates the app tree, database, logs, temp dir, and user themes dir, then runs migration SQL from `assets/config/repo_updates.json`. [theme_builder_setup.py](/home/clive/PycharmProjects/ctk_theme_builder/theme_builder_setup.py):238 [theme_builder_setup.py](/home/clive/PycharmProjects/ctk_theme_builder/theme_builder_setup.py):563 [theme_builder_setup.py](/home/clive/PycharmProjects/ctk_theme_builder/theme_builder_setup.py):587 [assets/config/repo_updates.json](/home/clive/PycharmProjects/ctk_theme_builder/assets/config/repo_updates.json):1
- Theme palettes are mutable per-theme JSON files stored under `assets/palettes`, created, copied, saved, and deleted at runtime. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):589 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):852 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):1607 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):1871 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):1953
- User themes are already conceptually externalized, but the fallback path is still install-relative: `APP_HOME / 'user_themes'`. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):177 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):181
- Palette labels and cascade mappings are not stored in theme files. They come from DB tables `colour_palette_entries` and `colour_cascade_properties`, seeded from migrations. [theme_builder_setup.py](/home/clive/PycharmProjects/ctk_theme_builder/theme_builder_setup.py):272 [assets/config/repo_updates.json](/home/clive/PycharmProjects/ctk_theme_builder/assets/config/repo_updates.json):100 [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):405 [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):755 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):1228
- Static assets like control-panel themes, images, views, default theme/palette, and geometry metadata are read-only and good candidates to remain packaged. [view/geometry_dialog.py](/home/clive/PycharmProjects/ctk_theme_builder/view/geometry_dialog.py):127 [view/ctk_theme_preview.py](/home/clive/PycharmProjects/ctk_theme_builder/view/ctk_theme_preview.py):89

## What breaks under wheel/PyPI

- Fresh install import path will fail unless a DB already exists, because logger/preferences read DB-backed settings during import. [utils/loggerutl.py](/home/clive/PycharmProjects/ctk_theme_builder/utils/loggerutl.py):57
- Writes into `site-packages` would fail for:
  - DB under `assets/data`
  - palette JSON under `assets/palettes`
  - temp WIP files under `tmp`
  - listener/QA semaphore files under `assets/etc`
  - config dir creation under `assets/config`
- Preview launch would fail because it shells out to repo-installed launcher scripts instead of calling packaged code directly. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):2465
- The current ZIP installer/build flow is not relevant to wheel distribution and would need to be replaced for end users. [theme_builder_setup.py](/home/clive/PycharmProjects/ctk_theme_builder/theme_builder_setup.py):595

## Python namespacing

The migration plan also needs to account for Python package namespacing and import layout.

Current risks:

- The source tree has been consolidated under `ctk_tb`, but launch still depends on direct script execution and repo-root `PYTHONPATH` handling rather than installed package entry points.
- Startup currently relies on repo-root path injection in [ctk_tb/controller/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/ctk_tb/controller/ctk_theme_builder.py):17 and launcher-managed `PYTHONPATH` in [ctk_theme_builder.sh](/home/clive/PycharmProjects/ctk_theme_builder/ctk_theme_builder.sh):14.
- Packaging metadata and installed entry points still need to be aligned with the application-owned namespace.

Recommended end state:

- Keep the distribution name as `ctk-theme-builder`.
- Keep the user data directory as `~/CTkThemeBuilder`.
- Use `ctk_tb` as the internal Python package namespace.

Example target layout:

- `ctk_tb/controller/...`
- `ctk_tb/model/...`
- `ctk_tb/view/...`
- `ctk_tb/utils/...`

Sequencing note:

- This namespacing change is important for a robust installed package, but it does not need to block Milestone 1 if the bootstrap refactor can be completed first with minimal import-path disruption.
- It should still be treated as a required packaging-hardening step before final wheel/PyPI completion.

Status note:

- The in-repo namespace consolidation to `ctk_tb/` is complete.
- Remaining work is to wire packaging metadata and console scripts to that namespace and remove the remaining launcher-time path manipulation.

## Breakage coverage

Each identified wheel/PyPI breakage must be mitigated by a corresponding mandatory change:

- Import-time failure on fresh install
  - Mitigation: add startup bootstrap that creates the user data root and initializes or upgrades the user-state DB before any DB-backed preferences are read.
  - Required implementation detail: remove import-time DB lookups from modules such as [utils/loggerutl.py](/home/clive/PycharmProjects/ctk_theme_builder/utils/loggerutl.py) and defer preference loading until after bootstrap.
- Writes into installed package directories
  - Mitigation: move all mutable state under `~/CTkThemeBuilder`.
  - Required implementation detail: no runtime writes may remain under package-relative `assets/*` or repo-relative `tmp`.
- Preview-process launch via repo scripts
  - Mitigation: replace `.sh`/`.bat` launch flow with package entry points or `python -m ...` subprocess invocation.
  - Required implementation detail: preview startup must not depend on files like `ctk_theme_builder.sh` being present beside the installed package.
- External ZIP installer dependency
  - Mitigation: move bootstrap, DB initialization, and migration logic into the application startup path.
  - Required implementation detail: a fresh wheel install must be runnable without `theme_builder_setup.py`.
- Static palette metadata living in DB only
  - Mitigation: choose one of two supported end states and implement it fully:
  - either keep palette labels and cascade mappings in the user DB as bootstrap-seeded static data
  - or move them to packaged JSON and stop requiring those DB tables at runtime
  - Required implementation detail: this cannot remain undecided, because first-run behavior depends on it.

## Palette coupling

Palette data is not coupled to `user_themes` inside the DB, but it is coupled at runtime by filename convention: each user theme expects a mutable palette file with the same basename. That means per-theme palette color data is runtime-writable and should move under `~/CTkThemeBuilder`.

The palette labels and cascade rules are different. They are global metadata, not user-authored theme content. They do not need to be writable at runtime unless you want users to edit palette structure. I would keep them packaged, or at most seed them into the user DB on first run.

## Recommended resource split

Keep packaged:

- `assets/images`
- `assets/views`
- `assets/themes` used as built-in control-panel themes
- `assets/etc/default_theme.json`
- `assets/etc/default_palette.json`
- `assets/etc/geometry_parameters.json`
- `assets/config/repo_updates.json` or replacement seed files

Move to `~/CTkThemeBuilder`:

- `themes/` for user-created/imported themes
- `palettes/` for per-theme palette JSON
- `state/ctk_theme_builder.db` for preferences, window geometry, autosave, and any remaining metadata tables
- `tmp/` for WIP preview files and semaphore/state files
- `logs/` for runtime logs

Optional:

- If you want starter editable themes on first install, copy selected bundled examples into `~/CTkThemeBuilder/themes` and matching palettes into `~/CTkThemeBuilder/palettes`.
- If not, start with an empty user theme dir and rely on "New Theme" from packaged `default_theme.json`.

## Concrete changes

Mandatory changes:

- Add an application-paths layer, for example `paths.py`, with explicit APIs for packaged assets and user data.
- Stop deriving mutable paths from `APP_HOME`; use `Path.home() / "CTkThemeBuilder"` for user data.
- Refactor direct path constants in [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):25 and [model/preferences.py](/home/clive/PycharmProjects/ctk_theme_builder/model/preferences.py):12 to use that layer.
- Move bootstrap into app startup:
  - create `~/CTkThemeBuilder/{themes,palettes,state,tmp,logs}`
  - create or upgrade the DB if missing
  - seed defaults and migrations without `theme_builder_setup.py`
- Remove import-time DB dependence from logger and preference setup. This is a required startup fix, not optional cleanup. [utils/loggerutl.py](/home/clive/PycharmProjects/ctk_theme_builder/utils/loggerutl.py):57
- Replace preview process launch with Python entry points:
  - `ctk-theme-builder` for the control panel
  - internal preview entry point or direct subprocess `python -m ...`
- Add console scripts in packaging metadata.
- Package data files in the wheel and access them via `importlib.resources` or equivalent, not `APP_HOME / "assets"`.
- Replace `APP_HOME / 'user_themes'` fallback with `~/CTkThemeBuilder/themes`. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):181
- Move palette file operations to `~/CTkThemeBuilder/palettes`. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):589 [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):852
- Move WIP theme preview files and semaphore files out of install assets. [view/control_panel.py](/home/clive/PycharmProjects/ctk_theme_builder/view/control_panel.py):1569 [model/ctk_theme_builder.py](/home/clive/PycharmProjects/ctk_theme_builder/model/ctk_theme_builder.py):43
- Choose and implement one static-metadata strategy:
  - keep palette labels and cascade metadata in the user DB as bootstrap-seeded static data
  - or move those definitions to packaged JSON and remove the runtime dependency on DB tables for them
- Consolidate imports under an application-owned Python namespace, with `ctk_tb` as the recommended internal package name, so the installed app no longer depends on generic top-level package names or `sys.path` surgery.

Recommended follow-on changes:

- Keep `theme_builder_setup.py` only as a legacy migration/import tool, or retire it entirely once wheel startup bootstrap is complete.
- Consider seeding bundled starter themes and palettes into the user data directory on first run if you want a non-empty initial experience.

## Migration plan

1. Introduce path abstraction and packaged-data loading without changing user-visible behavior.
2. Add startup bootstrap to create `~/CTkThemeBuilder` and initialize or upgrade the user-state DB before any DB-backed preferences are consumed.
3. Move mutable files:
   - themes to `~/CTkThemeBuilder/themes`
   - palettes to `~/CTkThemeBuilder/palettes`
   - DB, logs, tmp files, and semaphores to user data
4. Refactor logger and preferences so startup works with no preexisting DB and no import-time DB dependency.
5. Add wheel metadata and console scripts; remove dependency on `.sh`/`.bat` launchers for installed use.
6. Replace preview startup with package entry points or `python -m ...` so it no longer depends on repo-relative launch scripts.
7. Decide where palette labels and cascade metadata live in the wheel design, and implement that end state completely.
8. Move the codebase under an application-owned Python package namespace, with `ctk_tb` as the recommended internal import namespace, and remove repo-root path injection.
9. Keep `theme_builder_setup.py` only as a legacy migration/import tool, or retire it.
10. On first run, migrate legacy data if found:
   - copy old `user_themes/`
   - copy old `assets/palettes/`
   - copy old DB from `assets/data/ctk_theme_builder.db`
   - rewrite `theme_json_dir` preference to the new user-data path
11. Optionally seed starter themes and palettes into the new user directory if you want a non-empty first-run experience.

## Success criteria

The migration should be considered complete only when all of the following are true:

- `pip install` of the wheel succeeds and the app can be launched without running `theme_builder_setup.py`
- first run succeeds with no preexisting DB or user-data directory
- no runtime writes occur under the installed package directory
- control panel and preview panel both launch through package-managed entry points
- user themes and per-theme palettes persist under `~/CTkThemeBuilder`
- packaged static assets remain read-only inside the installed distribution

The main architectural change is simple: treat the wheel as read-only and move all mutable state behind a single user-data root. Once that is done, PyPI and wheel distribution become straightforward.
