# Contributing to ZeroEye

Thank you for your interest in contributing to ZeroEye! This document provides guidelines and instructions for setting up your development environment and submitting contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Build Instructions](#build-instructions)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Security](#security)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to professional, respectful collaboration. Please be constructive and respectful in all interactions.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/zeroeye.git
   cd zeroeye
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye.git
   ```

## Development Environment Setup

ZeroEye is a multi-language project. You only need to set up the components you plan to work on.

### Prerequisites

All modules require:
- Python 3 (for build tooling)
- Git

### Module-Specific Setup

#### Backend (Rust)
```bash
sudo apt update
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
cargo fetch
```

#### Frontend (TypeScript / React)
```bash
sudo apt update
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
npm install
```

#### Market (Go)
```bash
sudo apt update
sudo apt install -y golang-go
go mod download
```

#### Frailbox (C)
```bash
sudo apt update
sudo apt install -y build-essential make gcc linux-libc-dev
```

#### Engine (C++)
```bash
sudo apt update
sudo apt install -y build-essential g++ cmake
# If Ubuntu's cmake is older than 3.28:
sudo snap install cmake --classic
```

#### Compliance (Java)
```bash
sudo apt update
sudo apt install -y openjdk-21-jdk
```

#### Market V2 (Ruby)
```bash
sudo apt update
sudo apt install -y ruby-full ruby-dev build-essential redis-server
gem install eventmachine em-websocket-client redis sinatra
```

#### Scans (Lua)
```bash
sudo apt update
sudo apt install -y lua5.4 luarocks build-essential libi2c-dev i2c-tools
sudo luarocks install periphery
sudo luarocks install crypto
```

#### OpenAPI (Haskell)
```bash
sudo apt update
sudo apt install -y ghc cabal-install zlib1g-dev
cabal update
cabal install aeson text unordered-containers bytestring time directory filepath random network wai warp wai-logger http-types yaml aeson-keymap
```

#### OpenAPI Tools (Lua)
```bash
sudo apt update
sudo apt install -y lua5.4 luarocks build-essential
sudo luarocks install lua-yaml
sudo luarocks install http
sudo luarocks install crypto
```

### Quick Setup (All Modules)

To install dependencies for all modules at once:

```bash
sudo apt update
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config libssl-dev protobuf-compiler make gcc g++ cmake linux-libc-dev openjdk-21-jdk golang-go ruby-full ruby-dev redis-server lua5.4 luarocks libi2c-dev i2c-tools ghc cabal-install zlib1g-dev
```

## Build Instructions

The project uses a Python-based build system:

```bash
# Basic build
python3 build.py

# Build with diagnostics
python3 build.py --diagnostic

# Build specific module
python3 build.py --module backend
```

Build outputs and diagnostics are stored in the `diagnostic/` directory.

## Testing

Run tests for the modules you've modified:

```bash
# Backend tests
cd backend && cargo test

# Frontend tests
cd frontend && npm test

# Market tests
cd market && go test ./...
```

## Submitting Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: descriptive commit message"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request against the main repository

### Commit Message Format

We follow conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `security:` Security-related changes

## Security

For security-related issues, please review our security documentation and follow responsible disclosure practices.

## Questions?

Feel free to open an issue for questions or join our discussions.

---

Thank you for contributing to ZeroEye!
