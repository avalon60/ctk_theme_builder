# Release Artefact Guide

This project now uses Poetry for development dependency management and release building. The release flow produces:

- a source distribution (`sdist`)
- a wheel
- a generated `requirements.txt`
- a bundled release ZIP containing the above plus checksums and this guide

## Prerequisites

- Python 3.12 available locally
- Poetry installed locally
- Working directory set to the project root

## 1. Go to the project root

```bash
cd /home/clive/PycharmProjects/ctk_theme_builder
```

## 2. Ensure Poetry is using the intended Python version

```bash
poetry env use /home/clive/.pyenv/versions/3.12.0/bin/python
```

## 3. Install or sync dependencies

```bash
poetry install
```

## 4. Optional: verify the project metadata and exported dependency set

```bash
poetry check
poetry export --format requirements.txt --without-hashes --output requirements.txt
```

## 5. Confirm the application version matches the release version

The packaging script checks the version in both:

- `ctk_tb/model/ctk_theme_builder.py`
- `pyproject.toml`

Example check:

```bash
rg "__version__" ctk_tb/model/ctk_theme_builder.py
rg '^version = ' pyproject.toml
```

## 6. Build the release artefact

Replace `3.2.0` with the version you are releasing.

```bash
./utils/package.sh -v 3.2.0
```

## 7. Find the generated ZIP file

The build products are written under `dist/`.

```bash
ls -l /home/clive/PycharmProjects/ctk_theme_builder/dist
ls -l /home/clive/PycharmProjects/ctk_theme_builder/dist/ctk-theme-builder-3.2.0-release.zip
```

## Notes

- `requirements.txt` is generated from Poetry during packaging.
- `poetry check` runs before the build.
- `poetry build` produces both the wheel and source distribution.
- The bundled release ZIP is assembled from `dist/release/`.
- Poetry is required on the build machine only.
