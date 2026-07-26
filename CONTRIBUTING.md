# Contributing to Tent of Trials

## Local Setup

Clone the repository:

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye
cd zeroeye
```

Install the dependencies for the modules you plan to work on. See the [README](README.md#getting-started) for per-language dependency lists, or install everything at once:

```bash
sudo apt update
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config libssl-dev protobuf-compiler make gcc g++ cmake linux-libc-dev openjdk-21-jdk golang-go ruby-full ruby-dev redis-server lua5.4 luarocks libi2c-dev i2c-tools ghc cabal-install zlib1g-dev
```

## Build

```bash
python3 build.py                  # Build all modules
python3 build.py --module backend # Build a specific module
python3 build.py --clean          # Clean all artifacts
python3 build.py --release        # Release mode (Rust only)
```

Each build writes diagnostic files to `diagnostic/`. These are required for PR submission — see the [README](README.md#build-diagnostics) for details.

## Pull Request Workflow

1. **Fork** the repository
2. **Branch** from `main` with a descriptive name (`feat/...`, `fix/...`, `docs/...`)
3. **Commit** your changes with clear messages
4. **Run** `python3 build.py` to generate diagnostics
5. **Push** your branch and open a PR against `main`

Please use the [pull request template](.github/pull_request_template.md) when submitting.

## Code Style

This project uses [EditorConfig](https://editorconfig.org) to maintain consistent formatting. See [.editorconfig](.editorconfig) for language-specific rules — indentation, charset, and line endings are configured there.

## Bounties

Active bounties are tracked as GitHub issues. Look for the `bounty` label on the [Issues](https://github.com/cuentaprueba244w-dotcom/zeroeye/issues) page.
