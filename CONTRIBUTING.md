# Contributing to Tent of Trials

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to Tent of Trials. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Clone & Setup](#clone--setup)
  - [Build All Modules](#build-all-modules)
- [Development Workflow](#development-workflow)
  - [Branching](#branching)
  - [Making Changes](#making-changes)
  - [Testing](#testing)
  - [Build Validation](#build-validation)
- [Pull Request Process](#pull-request-process)
- [Style Guides](#style-guides)
  - [Git Commit Messages](#git-commit-messages)
  - [Code Style](#code-style)
- [Issue & Bounty Guidelines](#issue--bounty-guidelines)
- [Additional Resources](#additional-resources)

---

## Code of Conduct

This project is governed by a standard code of conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the repository maintainers.

## Getting Started

### Prerequisites

Tent of Trials is a multi-language monorepo. Depending on which module(s) you plan to touch, you'll need some or all of the following:

| Module | Language | Required Tooling |
|--------|----------|------------------|
| Backend | Rust | `rustc`, `cargo` (via rustup) |
| Frontend | TypeScript / React | Node.js 22+, npm |
| Market | Go | Go 1.21+ |
| Frailbox | C | `make`, `gcc` |
| Engine | C++ | `cmake 3.28+`, `g++` |
| Compliance | Java | OpenJDK 21+ |
| v2 Market Stream | Ruby | Ruby 3+, bundler |
| NFC Scanner | Lua | Lua 5.4, luarocks |
| OpenAPI (Haskell) | GHC, cabal-install |
| OpenAPI Tools | Lua | Lua 5.4, luarocks |

A quick way to install everything on Ubuntu/Debian:

```bash
sudo apt update && sudo apt install -y \
  build-essential curl ca-certificates gnupg pkg-config libssl-dev \
  protobuf-compiler make gcc g++ cmake linux-libc-dev openjdk-21-jdk \
  golang-go ruby-full ruby-dev redis-server lua5.4 luarocks \
  libi2c-dev i2c-tools ghc cabal-install zlib1g-dev
```

For Rust specifically:

```bash
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
```

For Node.js:

```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### Clone & Setup

```bash
# Clone the repository
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye
cd zeroeye

# Install Python dependencies (required for build.py)
pip install -r requirements.txt   # if available, or just ensure python3 is installed

# For frontend work
cd frontend && npm install && cd ..

# For backend work
cd backend && cargo fetch && cd ..
```

### Build All Modules

The canonical way to validate a full build is through the build script:

```bash
python3 build.py
```

This script walks through every module in the monorepo, builds each one, and writes a diagnostic log to `diagnostic/build-<commit-hash>.logd`. Include this diagnostic output in your pull request per the [Pull Request Process](#pull-request-process) below.

You can also build individual modules:

```bash
# Backend
cd backend && cargo build

# Frontend
cd frontend && npm run build

# Market
cd market && go build -o market .

# Frailbox (C)
cd frailbox && make

# Engine (C++)
cd frailbox/engine && cmake --build build

# Compliance (Java)
cd compliance && javac -d build ComplianceAuditor.java
```

## Development Workflow

### Branching

Create a feature branch from `main` (or the latest stable branch):

```bash
git checkout -b fix/your-fix-description
```

Use a descriptive branch name that reflects what you're working on:

- `fix/` for bug fixes
- `feat/` for new features
- `docs/` for documentation changes
- `chore/` for tooling/config changes

### Making Changes

1. Keep changes scoped to the purpose of your issue or bounty. Avoid unrelated cleanup.
2. Write tests for new functionality when applicable.
3. Ensure existing tests still pass.
4. Run the build locally before committing (see [Build Validation](#build-validation)).

### Testing

- **Backend (Rust):** `cd backend && cargo test`
- **Frontend (TypeScript):** `cd frontend && npm test`
- **Market (Go):** `cd market && go test ./...`

### Build Validation

Before submitting, always run:

```bash
python3 build.py
```

This will generate a diagnostic artifact at `diagnostic/build-<commit>.logd` (and possibly `diagnostic/build-<commit>.json`). These files prove your build passes on your local environment and are required in your PR.

## Pull Request Process

1. **Fork the repository** (if you're not a direct contributor) and create your feature branch.
2. **Make your changes** on the feature branch.
3. **Run `python3 build.py`** and verify all modules build cleanly.
4. **Write or update tests** as needed for your changes.
5. **Commit your changes** with a clear commit message (see [Git Commit Messages](#git-commit-messages)).
6. **Push your branch** to your fork.
7. **Open a pull request** against the `main` branch, using the [pull request template](.github/pull_request_template.md).
8. **Include the diagnostic artifact** (`diagnostic/build-*.logd` and `diagnostic/build-*.json` if present) in your PR — this is required for bounty submissions.
9. **Respond to review feedback** and update your PR as needed.

Your PR must include all of the following to be considered:

- A clear summary of what the PR does and why
- A list of notable changes
- A description of what local testing was done and the results
- Completed checklist items from the pull request template
- Diagnostic build logs committed in the PR

### Quick Checklist

- [ ] Forked and created a feature branch
- [ ] Changes are scoped to the issue/bounty purpose
- [ ] Build passes locally (`python3 build.py`)
- [ ] All tests pass
- [ ] Diagnostic artifact is committed
- [ ] PR template is filled out completely
- [ ] Commit messages are clear and descriptive

## Style Guides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

### Code Style

The project spans multiple languages, each with its own conventions:

- **Rust:** Standard `rustfmt` formatting with default settings
- **TypeScript:** Follow the existing patterns in `frontend/src/`
- **Go:** Standard `gofmt` formatting
- **C/C++:** Follow existing style in `frailbox/` and `frailbox/engine/`
- **General:** Match the style of the code you're modifying

## Issue & Bounty Guidelines

### Finding Work

Bountied issues are tagged with the `bounty` label along with a dollar amount in the title. Look for:

- Issues with `help wanted` and `good first issue` labels for easier starting points
- Issues that match your language/domain expertise
- Unassigned issues (someone may already be working on it, so leave a comment to claim it)

### Submitting for a Bounty

1. Comment on the issue to express interest.
2. Follow the standard PR process above.
3. Ensure the diagnostic build log is included — bounty reviewers rely on it for verification.

## Additional Resources

- [Project README](README.md) — overview and full setup instructions
- [Pull Request Template](.github/pull_request_template.md) — use this for all PR submissions
- [Architecture Overview](docs/ARCHITECTURE.md) — high-level system design
- [API Reference](docs/API_REFERENCE.md) — API documentation
- [Changelog](docs/CHANGELOG.md) — release history
