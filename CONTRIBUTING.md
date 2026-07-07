# Contributing to Tent of Trials

Thank you for your interest in contributing! This is a polyglot trading and risk platform with modules in Rust, TypeScript, Go, C, C++, Java, Ruby, Lua, and Haskell.

## Quick Start

### Prerequisites

See the [README](README.md#getting-started) for full dependency installation instructions per language.

### Setup

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
python3 build.py          # Build all modules
python3 build.py --list   # See available modules
```

## Development Workflow

1. **Fork** the repository on GitHub.
2. **Create a branch** for your changes:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. **Make changes** following the code style defined in `.editorconfig`.
4. **Run the build** to verify your changes compile:
   ```bash
   python3 build.py              # Build all modules
   python3 build.py -m backend   # Build only backend (Rust)
   python3 build.py -m frontend  # Build only frontend (TypeScript)
   ```
5. **Include diagnostic artifacts** – the build generates required diagnostic files under `diagnostic/`. These must be committed in your PR:
   ```bash
   python3 build.py -m frontend  # Generates diagnostic/build-<commit>.logd and .json
   git add diagnostic/
   ```
6. **Commit and push**:
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   git push origin feat/your-feature-name
   ```
7. **Open a Pull Request** against the `main` branch.

## Pull Request Guidelines

- Reference the issue number if your PR addresses a bounty or bug report.
- Include the generated diagnostic `.logd` and `.json` files (required by CI).
- Keep changes focused on a single concern.
- Update documentation if you add or change functionality.
- Ensure all existing tests and builds pass.

## Code Style

This project uses `.editorconfig` to maintain consistent formatting across all languages. Please ensure your editor supports EditorConfig (most modern editors do).

| Language | Indent | Style |
|----------|--------|-------|
| Python | 4 spaces | PEP 8 |
| Rust | 4 spaces | rustfmt |
| TypeScript/JavaScript | 2 spaces | Prettier |
| Go | tabs | gofmt |
| C | 4 spaces | K&R |
| C++ | 4 spaces | LLVM |
| Java | 4 spaces | Google Style |
| Ruby | 2 spaces | Rubocop |
| Lua | 2 spaces | luacheck |
| Haskell | 2 spaces | stylish-haskell |
| YAML/JSON/Markdown | 2 spaces | — |

## Reporting Issues

- Use GitHub Issues to report bugs or suggest features.
- For bounty issues, check the `bounty` label on open issues.
- Include reproduction steps, expected behavior, and actual behavior for bug reports.

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

## Questions?

Open a discussion or comment on the relevant issue.
