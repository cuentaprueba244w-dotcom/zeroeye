# Schemas

This directory contains JSON Schemas for project configuration files.

## Frontend package configuration

`frontend-package.schema.json` describes the expected structure for
`frontend/package.json`, including required Vite scripts, module mode, and
runtime/development dependency maps.

Example payloads live in `schemas/examples/`:

- `frontend-package.current.json` mirrors the current frontend package config.
- `frontend-package.minimal.json` keeps a smaller valid sample for regression checks.

Validation command:

```sh
npx --yes ajv-cli validate --spec=draft2020 \
  -s schemas/frontend-package.schema.json \
  -d schemas/examples/frontend-package.minimal.json \
  -d schemas/examples/frontend-package.current.json \
  -d frontend/package.json
```
