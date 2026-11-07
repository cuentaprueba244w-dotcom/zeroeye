# Contributing to Tent of Trials (zeroeye)

First off, thank you for considering contributing to our project! It's people like you that make this platform such a great open-source project.

## 1. Local Setup & Cloning

To get started with your contribution, you will need to clone the repository to your local machine:

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/zeroeye.git
cd zeroeye

# Add the upstream repository
git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye.git
```

## 2. Dependencies and Build Instructions

The project uses a multi-language build system (`build.py`) that orchestrates compilation across Rust, TypeScript, Go, C, C++, Java, Ruby, Lua, and Haskell. You do not need to install every language toolchain unless you are editing modules in that language. The build script skips missing modules gracefully.

To build the project:

```bash
# Build all modules
python3 build.py

# Build a specific module
python3 build.py -m frontend
python3 build.py -m backend,market

# Clean build artifacts
python3 build.py --clean
```

### Diagnostic Build Log
When you run `python3 build.py`, the system generates a diagnostic `.logd` and `.json` artifact in the `diagnostic/` directory (e.g., `diagnostic/build-XXX.logd`). This log proves that your local build succeeded and is **required** to be attached to your Pull Request submission.

## 3. Pull Request Workflow

We follow the standard GitHub workflow for open-source contributions:

1. **Fork the repository** on GitHub.
2. **Create a new branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. **Make your changes** and test them locally.
4. **Commit your changes** with a clear and descriptive commit message.
5. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```
6. **Open a Pull Request** against our `main` branch.

## 4. Code Style & Standards

We use EditorConfig to maintain consistent coding styles across various editors and IDEs. Please ensure your editor supports `.editorconfig` (either natively or via a plugin) so that your code formatting matches the project requirements automatically.

## 5. Pull Request Template

When opening a Pull Request, please ensure you use our standard template. You can view the template here: [.github/pull_request_template.md](.github/pull_request_template.md). This template contains a checklist ensuring you have provided the diagnostic log and followed required guidelines.

We look forward to reviewing your contributions!
