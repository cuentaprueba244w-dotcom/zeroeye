# Contributing to Tent of Trials

Thank you for considering contributing to the Tent of Trials project!  
This guide will help you get started with local development, building, and submitting your changes.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
  - [Clone the Repository](#clone-the-repository)
  - [Install Dependencies](#install-dependencies)
  - [Building the Project](#building-the-project)
- [Making Changes](#making-changes)
  - [Branch Naming](#branch-naming)
  - [Code Style](#code-style)
  - [Commit Messages](#commit-messages)
- [Submitting a Pull Request](#submitting-a-pull-request)
  - [Pull Request Template](#pull-request-template)
  - [Diagnostic Artifacts](#diagnostic-artifacts)
- [Need Help?](#need-help)

---

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](./CODE_OF_CONDUCT.md). By participating you agree to abide by its terms.

## Getting Started

### Clone the Repository

git clone https://github.com/lobster-trap/TentOfTrials
cd TentOfTrials
### Install Dependencies

Each major component has its own dependencies. Refer to the sections below for your area of interest:

- **Python (repo tooling)** – `python3` is required for `build.py`.
- **Backend (Rust)** – Install Rust via `rustup`, then run `cargo fetch` inside `backend/`.
- **Frontend (TypeScript)** – Node.js 22.x and npm, then `npm install` inside `frontend/`.
- **Market (Go)** – Go 1.21+ and `go mod download` inside `market/`.
- **Compliance (Java)** – OpenJDK 21.
- **Other components** – See [README.md](./README.md) for detailed instructions.

### Building the Project

The main build is driven by a Python script. Run from the repository root:

python3 build.py
This will compile all modules and generate diagnostic artifacts in the `diagnostic/` directory.  
If the build succeeds, you will find:

- `diagnostic/build-<timestamp>.logd` (always)
- `diagnostic/build-<timestamp>.json` (if present)

> **Note:** Ensure you have all required toolchains installed (Rust, Node, Go, etc.) before running the build.

## Making Changes

### Branch Naming

We use the naming convention `feature/your-feature-name` or `fix/your-fix-name`.  
Never commit directly to `main`.

### Code Style

This project uses an `.editorconfig` file ([.editorconfig](.editorconfig)) to maintain consistent formatting across editors. Please ensure your editor supports EditorConfig (most modern IDEs do).

For language‑specific style:

- **Rust**: `cargo fmt` and `cargo clippy` (run inside `backend/`).
- **TypeScript/JavaScript**: ESLint and Prettier (configured in `frontend/`).
- **Go**: `gofmt` and `golint`.
- **Java**: follow Google Java Style (see [checkstyle.xml](compliance/docs/checkstyle.xml) if present).

### Commit Messages

Write concise, descriptive commit messages. Use the imperative mood (e.g., "Add validation for market data").  
Reference any related issue or PR number when applicable.

## Submitting a Pull Request

1. **Fork** the repository to your GitHub account.
2. **Create a branch** from `main` following the naming convention above.
3. **Make your changes** and commit them with clear messages.
4. **Push** your branch to your fork.
5. **Open a Pull Request** against the `main` branch of the original repository.

### Pull Request Template

You must use the pull request template located at `.github/pull_request_template.md`.  
When creating your PR, the template will be automatically loaded. Fill in all required sections.

### Diagnostic Artifacts

After running `python3 build.py` locally, include the generated `.logd` file (and `.json` if present) as part of your PR.  
These files help reviewers understand the build state and diagnose any issues.  
Attach them to the PR description or include them in the PR’s `diagnostic/` directory.

## Need Help?

If you have questions or run into issues, please open a discussion or an issue in the repository.  
We appreciate your contribution!

---

Thank you for helping improve Tent of Trials.