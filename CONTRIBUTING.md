# Contributing

Thank you for helping improve Tent of Trials. This guide explains the expected local setup, build checks, and pull request workflow for this repository.

## Clone And Branch

```sh
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
git switch -c your-topic-branch
```

Use a short branch name that describes the change, such as `fix-build-diagnostics` or `docs-contributing-guide`.

## Local Dependencies

The repository contains several language modules. Install the tools for the modules you plan to edit, then run the repository build before opening a pull request.

Required for the build driver:

```sh
python3 --version
```

Common module toolchains:

```sh
# Rust backend
cargo --version

# TypeScript frontend
node --version
npm --version

# Go market service
go version

# C and C++ modules
make --version
cmake --version

# Java compliance module
javac -version

# Ruby, Lua, and Haskell checks
ruby --version
lua -v
ghc --version
```

The README has fuller package-manager commands for installing these tools on a fresh system.

## Build Commands

Run the full build from the repository root:

```sh
python3 build.py
```

Useful targeted commands:

```sh
python3 build.py --list
python3 build.py --module backend
python3 build.py --module frontend,market
python3 build.py --clean
```

If your change affects only one module, run the focused module build first, then run the full build before submitting.

## Diagnostic Artifacts

`python3 build.py` writes encrypted diagnostic artifacts under `diagnostic/` using the current commit prefix:

```text
diagnostic/build-<commit>.json
diagnostic/build-<commit>.logd
```

Include the generated `.json` and `.logd` files in the pull request. The metadata JSON records module pass/fail counts and the decrypt command needed by reviewers. Maintainers may ask for diagnostic artifacts to be removed before merge.

## Code Style

Follow the repository `.editorconfig` settings when editing files. In general:

- Use UTF-8 text files with LF line endings.
- Keep a final newline at the end of text files.
- Avoid trailing whitespace.
- Use the indentation style defined by `.editorconfig` for the file type you are editing.

For formatting-only changes, keep them separate from functional changes whenever possible.

## Pull Request Workflow

1. Fork the repository.
2. Create a focused branch from `main`.
3. Make the smallest change that satisfies the issue or bounty acceptance criteria.
4. Run the relevant targeted checks.
5. Run `python3 build.py` and commit the required diagnostic artifacts.
6. Commit with a concise message.
7. Open a pull request against `main`.
8. Use the repository pull request template at `.github/pull_request_template.md`.

In the PR body, include:

- A short summary of the change.
- The notable files or behavior changed.
- Exact local commands run and their results.
- Any known unrelated local build failures.
- The diagnostic artifact paths committed in the PR.

## Review Expectations

Keep pull requests scoped to the issue being solved. Avoid unrelated refactors, generated build output, local caches, and dependency churn unless the issue explicitly requires them. If review feedback is actionable, update the same branch with a follow-up commit and rerun the relevant checks.
