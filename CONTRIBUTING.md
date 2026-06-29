# Contributing to ZeroEye

Thank you for your interest in contributing to ZeroEye!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/zeroeye.git
   cd zeroeye
   ```
3. Install dependencies (Python 3.12+ recommended):
   ```bash
   pip install -r requirements.txt
   ```
4. Run the build to verify:
   ```bash
   python3 build.py
   ```

## Development Workflow

- Create a branch for your changes: `git checkout -b feature/your-feature`
- Make focused, atomic commits
- Run `python3 build.py` to verify diagnostics are generated
- Ensure all existing tests pass

## Pull Request Guidelines

- Keep PRs focused on a single issue
- Reference the issue number in your PR description (e.g., "Closes #5")
- Include diagnostic build artifacts when applicable
- Be responsive to reviewer feedback

## Code Style

- Python: Follow PEP 8, include type hints
- TypeScript/JavaScript: Use 2-space indentation
- Rust: Use 4-space indentation
- Go: Use tabs
- YAML/JSON/Markdown: Use 2-space indentation

## Bounty Issues

Issues labeled with `bounty` have a monetary reward. Comment on the issue before starting work to confirm it's available.

## Questions?

Open a discussion or comment on the relevant issue.