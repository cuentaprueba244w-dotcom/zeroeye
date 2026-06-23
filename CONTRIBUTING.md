# Contributing to ZeroEye

Thank you for your interest in contributing to ZeroEye! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.10+ with pip
- Rust 1.70+ (for Rust modules)
- Node.js 18+ (for frontend modules)
- Git

### Local Setup

1. Fork the repository on GitHub.
2. Clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/zeroeye.git
cd zeroeye
```

3. Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scriptsctivate
pip install -r requirements.txt  # if exists
```

4. Verify your setup by running the build:

```bash
python3 build.py
```

## Development Workflow

1. Create a feature branch from `main`:

```bash
git checkout -b feat/your-feature-name
```

2. Make your changes following the project coding style (see `.editorconfig`).

3. Run the build to verify:

```bash
python3 build.py
```

4. Commit your changes with a descriptive message:

```bash
git commit -m "feat(#issue): description of changes"
```

5. Push to your fork:

```bash
git push origin feat/your-feature-name
```

6. Open a Pull Request against the `main` branch.

## Pull Request Guidelines

- Reference the issue number in your PR title and description (e.g., `Closes #123`)
- Keep PRs focused on a single concern
- Ensure `python3 build.py` completes successfully
- Include any relevant diagnostic output

## Code Style

This project uses `.editorconfig` for consistent formatting across languages. Most editors support it natively or via a plugin.

## Need Help?

Open an issue or ask in the project discussions.
