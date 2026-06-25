# Contributing to Tent of Trials

Thank you for your interest in contributing to Tent of Trials! This guide will help you get started.

## Getting Started

### Prerequisites

- Git
- Python 3.10+
- Rust 2021 (for backend)
- Node.js 22+ (for frontend)
- Go 1.21+ (for market module)

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/TentOfTrials
   cd TentOfTrials
   ```
3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye
   ```

### Development Setup

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
```

#### Compliance (Java)
```bash
sudo apt update
sudo apt install -y openjdk-21-jdk
```

### Build

Run the build script to generate diagnostic artifacts:
```bash
python3 build.py
```

## Pull Request Workflow

1. **Create a branch** from main:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit with a descriptive message:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a Pull Request** on GitHub:
   - Use the pull request template
   - Reference any related issues
   - Include diagnostic artifacts from `build.py`

## Code Style

- **Python**: Follow PEP 8, use Black formatter
- **Rust**: Use `cargo fmt`
- **TypeScript**: Use Prettier
- **Go**: Use `gofmt`

See `.editorconfig` for editor settings.

## Testing

- Run `python3 build.py` to generate diagnostic artifacts
- Include `.logd` and `.json` artifacts in your PR
- Ensure all existing tests pass

## Reporting Issues

- Use GitHub Issues for bug reports
- Include steps to reproduce
- Include environment details

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
