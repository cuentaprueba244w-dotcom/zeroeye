# Contributing to Tent of Trials

Thank you for your interest in contributing to Tent of Trials! This document describes how to set up your environment, build the project, and submit changes.

## Table of Contents

- [Getting Started](#getting-started)
- [Building the Project](#building-the-project)
- [Code Style](#code-style)
- [Pull Request Workflow](#pull-request-workflow)
- [Build Diagnostics](#build-diagnostics)
- [Module Overview](#module-overview)

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
```

### 2. Install Python (required for build system)

```bash
sudo apt update
sudo apt install python3
```

### 3. Install language toolchains

The project spans multiple languages. Install only the toolchains for the modules you plan to work on:

| Module | Language | Install Command |
|--------|----------|-----------------|
| backend | Rust | `curl https://sh.rustup.rs -sSf \| sh -s -- -y` |
| frontend | TypeScript | `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo -E bash - && sudo apt install -y nodejs` |
| market | Go | `sudo apt install -y golang-go` |
| frailbox | C | `sudo apt install -y build-essential make gcc` |
| engine | C++ | `sudo apt install -y build-essential g++ cmake` |
| compliance | Java | `sudo apt install -y openjdk-21-jdk` |
| v2/services | Ruby | `sudo apt install -y ruby-full` |
| nfc | Lua | `sudo apt install -y lua5.4 luarocks` |
| docs/openapi | Haskell | `sudo apt install -y ghc cabal-install` |

To install everything at once:

```bash
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config \
  libssl-dev protobuf-compiler make gcc g++ cmake linux-libc-dev \
  openjdk-21-jdk golang-go ruby-full ruby-dev redis-server \
  lua5.4 luarocks libi2c-dev i2c-tools ghc cabal-install zlib1g-dev
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Fetch backend dependencies

```bash
cd backend
cargo fetch
cd ..
```

## Building the Project

Use the unified build system to compile all modules:

```bash
python3 build.py                          # Build all modules
python3 build.py -m backend,frontend      # Build specific modules
python3 build.py --release                # Release mode (Rust only)
python3 build.py --clean                  # Clean all build artifacts
python3 build.py --list                   # List available modules
python3 build.py --verbose                # Verbose output
```

### Available Modules

| Module | Language | Build Command |
|--------|----------|---------------|
| backend | Rust | `cargo build` |
| frontend | TypeScript | `npm run build` |
| market | Go | `go build -o market .` |
| frailbox | C | `make` |
| engine | C++ | `cmake --build build` |
| compliance | Java | `javac -d build ComplianceAuditor.java` |
| v2-market-stream | Ruby | `ruby -c market_stream.rb` |
| nfc-scanner | Lua | `luac -p scanner.lua` |
| openapi-haskell | Haskell | `ghc -fno-code Types.hs Server.hs Validate.hs Generate.hs` |
| openapi-tools | Lua | `luac -p openapi_diff.lua openapi_mock.lua openapi_pact.lua` |

## Code Style

This project uses an `.editorconfig` file to enforce consistent formatting across all languages. Ensure your editor has EditorConfig support enabled.

Key conventions:

- **Python**: 4-space indentation, UTF-8, LF line endings
- **Rust**: 4-space indentation, UTF-8, LF line endings
- **TypeScript/JavaScript**: 2-space indentation, UTF-8, LF line endings
- **Go**: Tab indentation, UTF-8, LF line endings
- **Makefile**: Tab indentation, UTF-8, LF line endings
- **YAML**: 2-space indentation, UTF-8, LF line endings
- **JSON**: 2-space indentation, UTF-8, LF line endings
- **Markdown**: 2-space indentation, UTF-8, LF line endings

Global rules for all files:

- Charset: UTF-8
- Line endings: LF
- Insert final newline: yes
- Trim trailing whitespace: yes

## Pull Request Workflow

Follow these steps to submit a pull request:

### 1. Fork the repository

Click the **Fork** button on the [repository page](https://github.com/cuentaprueba244w-dotcom/zeroeye).

### 2. Clone your fork and create a branch

```bash
git clone https://github.com/<your-username>/zeroeye.git
cd zeroeye
git checkout -b <descriptive-branch-name>
```

### 3. Make your changes

Write code, tests, or documentation following the [Code Style](#code-style) guidelines above.

### 4. Run the build

```bash
python3 build.py
```

Ensure the build generates diagnostic artifacts in the `diagnostic/` directory.

### 5. Commit your changes

```bash
git add .
git commit -m "<type>: <description of your change>"
```

Use conventional commit prefixes:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation
- `config:` configuration
- `refactor:` code refactoring
- `test:` test additions

### 6. Push and create a Pull Request

```bash
git push origin <descriptive-branch-name>
```

Open a pull request against the `main` branch. Use the [PR template](.github/pull_request_template.md) to structure your submission.

## Build Diagnostics

Every PR must include build diagnostic artifacts. Running `python3 build.py` generates:

- `diagnostic/build-<commit-id>.logd` - Encrypted diagnostic log
- `diagnostic/build-<commit-id>.json` - Metadata JSON report

Include both files in your PR. The JSON report contains:

- Build status (pass/fail counts)
- Per-module results with elapsed times
- Decrypt password for the `.logd` file
- Module build output logs

Maintainers may ask you to remove diagnostic artifacts before merging.

## Module Overview

| Directory | Description |
|-----------|-------------|
| `backend/` | Rust-based backend service |
| `frontend/` | TypeScript/React frontend application |
| `market/` | Go-based market data service |
| `frailbox/` | C-based sandbox runtime |
| `frailbox/engine/` | C++ physics engine |
| `compliance/` | Java compliance auditor |
| `v2/services/` | Ruby market stream service |
| `frailbox/nfc/` | Lua NFC scanner |
| `docs/openapi/` | Haskell OpenAPI tools |
| `tools/` | Lua OpenAPI utilities and encryptly binary |
| `data/` | Data files |
| `diagnostic/` | Build diagnostic artifacts |

## Questions

If you have questions, please [open an issue](https://github.com/cuentaprueba244w-dotcom/zeroeye/issues) or check existing [issues](https://github.com/cuentaprueba244w-dotcom/zeroeye/issues) for bounty opportunities.
