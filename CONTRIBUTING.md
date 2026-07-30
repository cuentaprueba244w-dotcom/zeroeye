# Contributing to Tent of Trials

Thank you for your interest in contributing to the Tent of Trials project! This document provides guidelines for setting up your local development environment, building the project, and submitting pull requests.

---

## Getting Started

### Cloning the Repository

```bash
git clone https://github.com/lobster-trap/TentOfTrials.git
cd TentOfTrials
```

### Prerequisites

Ensure you have the following tools installed:

- Python 3.8+ (for build scripts and tooling)
- Rust toolchain (for backend compilation)
- Go 1.21+ (for market engine)
- Node.js 18+ (for frontend)
- CMake 3.20+ (for frailbox engine)
- Make (for frailbox)
- Java JDK 21+ (for compliance module)
- Ruby (for market v2)
- Lua 5.4 (for openapi tools)
- GHC (Glasgow Haskell Compiler) (for openapi Haskell)
- `nvidia-smi` (optional, for GPU monitoring)

Refer to the `README.md` for detailed installation instructions.

---

## Building the Project

The project uses a unified Python build script to orchestrate builds across all modules.

### Build All Modules

```bash
python3 build.py
```

### Build Specific Modules

```bash
python3 build.py --module backend,frontend
```

### Clean Build Artifacts

```bash
python3 build.py --clean
```

### Release Build (Backend Only)

```bash
python3 build.py --release
```

### Verbose Output

```bash
python3 build.py --verbose
```

### List Available Modules

```bash
python3 build.py --list
```

---

## Pull Request Workflow

1. Fork the repository.
2. Create a feature branch from `main`.
3. Make your changes with clear, concise commit messages.
4. Run the build script and ensure all modules build successfully.
5. Include a diagnostic build log in the `diagnostic/` directory by running the build script.
6. Push your branch to your fork.
7. Open a pull request against the `main` branch.
8. Fill out the PR template with a summary, changes, testing, and checklist.
9. Address any review comments promptly.

---

## Code Style and Guidelines

- Follow existing code style and conventions.
- Write clear, maintainable code with comments where necessary.
- Add tests for new features or bug fixes.
- Avoid committing generated build artifacts except for diagnostic logs.
- Use `.editorconfig` for consistent formatting.

---

## Additional Resources

- [Pull Request Template](.github/pull_request_template.md)
- [Issue Tracker](https://github.com/lobster-trap/TentOfTrials/issues)
- [Code of Conduct](CODE_OF_CONDUCT.md) (if applicable)

---

Thank you for helping make Tent of Trials better!
