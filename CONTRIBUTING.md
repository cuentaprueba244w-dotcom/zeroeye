# Contributing to ZeroEye

Thank you for your interest in contributing to ZeroEye! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.x
- Rust (for backend)
- Node.js 22+ (for frontend)
- Git

### Clone and Setup

```bash
git clone https://github.com/your-username/zeroeye.git
cd zeroeye
```

### Backend Setup (Rust)

```bash
sudo apt update
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
cargo fetch
```

### Frontend Setup (TypeScript/React)

```bash
sudo apt update
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
npm install
```

### Build

```bash
python3 build.py
```

## Pull Request Workflow

1. **Fork** the repository
2. **Create a branch** from `main` for your changes
3. **Make your changes** following the code style in `.editorconfig`
4. **Commit** with a clear message describing your changes
5. **Push** to your fork
6. **Create a Pull Request** to the `main` branch

## Code Style

- Follow the `.editorconfig` rules for your language
- Python: 4 spaces
- Rust: 4 spaces
- TypeScript/JavaScript: 2 spaces
- Go: tabs
- YAML/JSON/Markdown: 2 spaces

## Testing

Run the build script to verify your changes:

```bash
python3 build.py
```

Include the generated diagnostic `.logd` artifact from `diagnostic/build-XXX.logd` in your PR.

## Pull Request Template

Use the `.github/pull_request_template.md` template when creating your PR.

## Questions?

If you have questions, feel free to open an issue or reach out to the maintainers.
