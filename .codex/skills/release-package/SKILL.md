---
name: release-package
description: Prepare a release artefact for this project by bumping the requested semantic version level and running the packaging script. Use when the user asks to bump a major, minor, or patch release and package or create a release artefact. Do not use for ordinary build or test tasks.
---

When this skill is used:
1. Determine whether the user explicitly requested `major`, `minor`, or `patch`.
2. Run exactly one of:
   - `./utils/bump_major.sh`
   - `./utils/bump_minor.sh`
   - `./utils/bump_patch.sh`
3. Then run:
   - `./utils/package.sh`
4. Report:
   - which bump command was run
   - the resulting version
   - the packaging result
   - the artefact path or filename if available

Safety rules:
- Use the release bump scripts as-is. They are allowed to commit and tag as part of an explicitly requested release operation.
- Do not run `git commit`, `git tag`, `git push`, or any bump script during ordinary development work unless I explicitly ask for a release operation.
- Do not guess the bump level.
- If packaging fails, report the failure and relevant output.
