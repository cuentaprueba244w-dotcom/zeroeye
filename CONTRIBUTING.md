# Contributing to ZeroEye

Thank you for your interest in contributing to ZeroEye! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Local Setup](#local-setup)
- [Building](#building)
- [Code Style](#code-style)
- [Pull Request Workflow](#pull-request-workflow)
- [Diagnostic Artifacts](#diagnostic-artifacts)

## Getting Started

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/zeroeye.git
   cd zeroeye
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye.git
   ```

## Prerequisites

### Python (Repo Tooling)

```bash
sudo apt update
sudo apt install python3
```

### Backend (Rust)

```bash
sudo apt update
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
```

### Frontend (TypeScript / React)

```bash
sudo apt update
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### Market (Go)

```bash
sudo apt update
sudo apt install -y golang-go
```

### Frailbox (C)

```bash
sudo apt update
sudo apt install -y build-essential make gcc linux-libc-dev
```

### Engine (C++)

```bash
sudo apt update
sudo apt install -y build-essential g++ cmake
# If Ubuntu's cmake is older than 3.28, install via snap:
sudo snap install cmake --classic
```

### Compliance (Java)

```bash
sudo apt update
sudo apt install -y openjdk-21-jdk
```

### Market v2 (Ruby)

```bash
sudo apt update
sudo apt install -y ruby ruby-dev
```

## Building

### Install Dependencies

```bash
# Python
pip install -r requirements.txt

# Rust
cargo fetch

# Node.js
npm install

# Go
go mod download

# Ruby
bundle install
```

### Run Build

```bash
python3 build.py
```

This will:
1. Build all modules
2. Generate diagnostic artifacts in `diagnostic/`
3. Create `.logd` and `.json` files

## Code Style

This project uses `.editorconfig` for code style. Please ensure your editor respects these settings.

Key rules:
- **Indentation**: 4 spaces for most files
- **Line endings**: LF (Unix)
- **Charset**: UTF-8
- **Trim trailing whitespace**: Yes
- **Insert final newline**: Yes

### Language-Specific Style

- **Python**: Follow PEP 8
- **Rust**: Use `cargo fmt`
- **TypeScript**: Use ESLint + Prettier
- **Go**: Use `gofmt`
- **C/C++**: Follow existing code style
- **Java**: Follow Google Java Style Guide

## Pull Request Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Write clean, well-documented code
- Follow the code style guidelines
- Add tests if applicable

### 3. Commit Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation
- `style:` for formatting
- `refactor:` for code refactoring
- `test:` for tests
- `chore:` for maintenance

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to the original repository
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR template (`.github/pull_request_template.md`)
5. Submit the PR

### 6. PR Requirements

- [ ] Code compiles without errors
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if applicable)
- [ ] Diagnostic artifacts included
- [ ] Follows code style guidelines

## Diagnostic Artifacts

When submitting a PR, include diagnostic artifacts from your build:

1. Run the build:
   ```bash
   python3 build.py
   ```

2. Locate artifacts in `diagnostic/`:
   ```
   diagnostic/build-XXX.logd
   diagnostic/build-XXX.json  (if present)
   ```

3. Include these files in your PR

## Questions?

If you have questions, feel free to:
- Open an issue
- Ask in the PR comments
- Check existing documentation

Thank you for contributing to ZeroEye!
