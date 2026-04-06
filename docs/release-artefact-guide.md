# Release Artefact Guide

This project now uses Poetry for development dependency management, while deployment artefacts are still built as a ZIP package containing a generated `requirements.txt`.

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

The packaging script checks the version in `model/ctk_theme_builder.py`.

Example check:

```bash
rg "__version__" model/ctk_theme_builder.py
```

## 6. Build the release artefact

Replace `3.1.0` with the version you are releasing.

```bash
./utils/package.sh -v 3.1.0
```

Compatibility wrapper:

```bash
./utils/tb-package.sh -v 3.1.0
```

## 7. Find the generated ZIP file

The archive is written to the sibling `stage` directory:

```bash
ls -l /home/clive/PycharmProjects/stage/ctk_theme_builder-3.1.0.zip
```

## Notes

- `requirements.txt` is generated from Poetry during packaging.
- Poetry is required on the build machine only.
- Poetry is not required on the target system.
- The target deployment model remains based on the packaged ZIP and `requirements.txt`.
