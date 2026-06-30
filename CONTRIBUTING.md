# Contributing to Zeroeye

Thank you for contributing. This guide covers local setup, building the project, and submitting pull requests.

## Local setup

### Clone the repository

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
```

If you do not have write access to the upstream repository, [fork](https://docs.github.com/en/get-started/quickstart/fork-a-repo) it on GitHub and clone your fork instead:

```bash
git clone https://github.com/<your-username>/zeroeye.git
cd zeroeye
git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye.git
```

### Install dependencies

Zeroeye is a multi-language monorepo. Install the toolchain for the modules you plan to change. On Ubuntu/Debian:

```bash
# Python (repo tooling)
sudo apt update
sudo apt install -y python3

# Backend (Rust)
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
cargo fetch

# Frontend (TypeScript / React)
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
cd frontend && npm install && cd ..

# market (Go)
sudo apt install -y golang-go
cd market && go mod download && cd ..

# frailbox (C)
sudo apt install -y build-essential make gcc linux-libc-dev

# engine (C++)
sudo apt install -y build-essential g++ cmake
# If Ubuntu's cmake is older than 3.28, install via snap:
sudo snap install cmake --classic

# compliance (Java)
sudo apt install -y openjdk-21-jdk

# market v2 (Ruby)
sudo apt install -y ruby-full ruby-dev build-essential redis-server
gem install eventmachine em-websocket-client redis sinatra

# nfc-scanner (Lua)
sudo apt install -y lua5.4 luarocks build-essential libi2c-dev i2c-tools
sudo luarocks install periphery
sudo luarocks install crypto

# openapi (Haskell)
sudo apt install -y ghc cabal-install zlib1g-dev
cabal update
cabal install aeson text unordered-containers bytestring time directory filepath random network wai warp wai-logger http-types yaml aeson-keymap

# openapi-tools (Lua)
sudo apt install -y lua5.4 luarocks build-essential
sudo luarocks install lua-yaml
sudo luarocks install http
sudo luarocks install crypto
```

To install packages for all modules at once:

```bash
sudo apt update
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config libssl-dev protobuf-compiler make gcc g++ cmake linux-libc-dev openjdk-21-jdk golang-go ruby-full ruby-dev redis-server lua5.4 luarocks libi2c-dev i2c-tools ghc cabal-install zlib1g-dev
```

See [README.md](README.md) for additional context on the project layout.

## Building

The unified build entry point is `build.py` at the repository root.

```bash
python3 build.py                              # Build all modules
python3 build.py --clean                      # Clean all artifacts
python3 build.py --module backend,frontend    # Build specific modules
python3 build.py --release                    # Release mode (Rust only)
python3 build.py --list                       # List available modules
python3 build.py --verbose                    # Verbose output
```

Available modules: `backend`, `frontend`, `market`, `frailbox`, `engine`, `compliance`, `v2-market-stream`, `nfc-scanner`, `openapi-haskell`, and `openapi-tools`.

### Build diagnostics

Each build writes a diagnostic bundle into the git-tracked `diagnostic/` directory:

- `diagnostic/build-<commit-4-bytes>.logd` — encrypted build log
- `diagnostic/build-<commit-4-bytes>.json` — metadata (decrypt password, module results)

The filename is derived from the first four bytes of the current `HEAD` commit, so it stays stable for a given commit.

**Before opening a PR**, run `python3 build.py` locally and commit the generated diagnostic files. Reviewers use these artifacts to verify your build environment. You may request removal of the diagnostic log before merge (see the PR template checklist).

## Code style

Follow the formatting rules in [`.editorconfig`](.editorconfig) at the repository root when editing files. EditorConfig is supported by most editors and IDEs; enable the EditorConfig plugin if your editor does not apply it automatically.

Keep changes scoped to the task at hand. Avoid unrelated refactors, drive-by formatting, or committing generated build artifacts except the required diagnostic files described above.

## Pull request workflow

1. **Fork** the repository on GitHub (skip if you already have direct write access).
2. **Branch** from `main` with a descriptive name:
   ```bash
   git checkout main
   git pull upstream main   # or origin main if working from a fork
   git checkout -b my-feature-branch
   ```
3. **Commit** your changes with clear messages. Run `python3 build.py` and include the diagnostic artifacts when your change affects buildable code.
4. **Push** your branch to your fork (or upstream if you have access):
   ```bash
   git push -u origin my-feature-branch
   ```
5. **Open a pull request** against `cuentaprueba244w-dotcom/zeroeye` `main`.

Use [`.github/pull_request_template.md`](.github/pull_request_template.md) when filling out your PR description. It covers the summary, testing notes, and checklist items maintainers expect (including the diagnostic build log).

For bounty submissions, reference the issue in the PR title (for example, `bounty #3`) and include `Closes #<issue>` in the description when appropriate.

## Bounties

Active bounties are tracked as GitHub issues labeled `bounty`. Browse the [Issues](https://github.com/cuentaprueba244w-dotcom/zeroeye/issues) page for open tasks, acceptance criteria, and payout details.

## Questions

For architecture and operational context, see the documents under [`docs/`](docs/). Open a GitHub issue if something in this guide is unclear or out of date.
