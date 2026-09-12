# Contributing to ZeroEye

Thank you for your interest in contributing! This guide covers local setup, building, and submitting changes.

## Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Rust** 1.70+ with Cargo
- **Python** 3.10+
- **Make** and a C/C++ toolchain (gcc/clang)
- **Java** 17+ (for compliance module)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
```

### 2. Install Dependencies

**Frontend:**
```bash
cd frontend
npm install
```

**Backend:**
```bash
cd backend
cargo build
```

**Python tools:**
```bash
pip install -r requirements.txt
```

**Frailbox (C/C++):**
```bash
cd frailbox
make
```

## Building

### Frontend
```bash
cd frontend
npm run build        # Production build to dist/
npm run dev          # Dev server on http://localhost:3000
```

### Backend
```bash
cd backend
cargo build --release
cargo run             # Runs on http://localhost:8080
```

### Frailbox
```bash
cd frailbox
make clean && make
./frailbox --help
```

## Code Style

This project uses [`.editorconfig`](.editorconfig) for consistent formatting. Ensure your editor supports EditorConfig or install the appropriate plugin.

- **TypeScript/JavaScript**: Follow existing patterns; use Prettier if available
- **Rust**: Run `cargo fmt` before committing
- **Python**: Follow PEP 8; run `black` or `ruff format` if configured
- **C/C++**: Follow the existing style in `frailbox/`

## Pull Request Workflow

### 1. Fork the Repository
Click "Fork" on GitHub to create your own copy.

### 2. Create a Feature Branch
```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Make Your Changes
- Write clear, focused commits
- Add tests if applicable
- Update documentation as needed

### 4. Push and Open a PR
```bash
git push origin feat/your-feature-name
```

Then open a Pull Request on GitHub. Fill out the [pull request template](.github/pull_request_template.md) completely.

## Questions?

Open an issue if you have questions or need clarification on any part of the codebase.