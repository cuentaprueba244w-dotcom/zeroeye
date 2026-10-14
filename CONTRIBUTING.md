# Contributing to Tent of Trials

Thanks for your interest in contributing. This guide covers local setup, build
commands, the pull-request workflow, and the diagnostic build log that every PR
must include.

Tent of Trials is a multi-language trading and risk platform. Each module is
written in a different language and built by a single top-level orchestrator,
`build.py`.

| Module | Language | Directory |
| --- | --- | --- |
| `backend` | Rust | `backend/` |
| `frontend` | TypeScript / React | `frontend/` |
| `market` | Go | `market/` |
| `frailbox` | C | `frailbox/` |
| `engine` | C++ | `frailbox/engine/` |
| `compliance` | Java | `compliance/` |
| `v2-market-stream` | Ruby | `v2/services/` |
| `nfc-scanner` | Lua | `frailbox/nfc/` |
| `openapi-haskell` | Haskell | `docs/openapi/` |
| `openapi-tools` | Lua | `tools/` |

---

## 1. Clone the repository

Fork the repository on GitHub, then clone **your fork** and add the upstream
repository as a second remote:

```sh
git clone https://github.com/<your-username>/zeroeye
cd zeroeye
git remote add upstream https://github.com/cuentaprueba244w-dotcom/zeroeye
git fetch upstream
```

Keep your fork in sync before starting new work:

```sh
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git push origin main
```

---

## 2. Install dependencies

You only need the toolchains for the modules you intend to touch, but the
build orchestrator itself requires **Python 3**.

```sh
# Build orchestrator (required)
sudo apt update && sudo apt install -y python3
```

Per-module dependencies:

```sh
# Backend (Rust)
sudo apt update
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
cargo fetch

# Frontend (TypeScript / React)
sudo apt update
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
npm install

# market (Go)
sudo apt update && sudo apt install -y golang-go
go mod download

# frailbox (C)
sudo apt update && sudo apt install -y build-essential make gcc linux-libc-dev

# engine (C++)
sudo apt update && sudo apt install -y build-essential g++ cmake
# If Ubuntu's cmake is older than 3.28, install via snap:
sudo snap install cmake --classic

# compliance (Java)
sudo apt update && sudo apt install -y openjdk-21-jdk

# market v2 (Ruby)
sudo apt update
sudo apt install -y ruby-full ruby-dev build-essential redis-server
gem install eventmachine em-websocket-client redis sinatra

# scans (Lua)
sudo apt update
sudo apt install -y lua5.4 luarocks build-essential libi2c-dev i2c-tools
sudo luarocks install periphery
sudo luarocks install crypto

# openapi (Haskell)
sudo apt update
sudo apt install -y ghc cabal-install zlib1g-dev
cabal update
cabal install aeson text unordered-containers bytestring time directory filepath random network wai warp wai-logger http-types yaml aeson-keymap

# openapi-tools (Lua)
sudo apt update
sudo apt install -y lua5.4 luarocks build-essential
sudo luarocks install lua-yaml
sudo luarocks install http
sudo luarocks install crypto
```

Install every module toolchain at once:

```sh
sudo apt update
sudo apt install -y build-essential curl ca-certificates gnupg pkg-config libssl-dev \
  protobuf-compiler make gcc g++ cmake linux-libc-dev openjdk-21-jdk golang-go \
  ruby-full ruby-dev redis-server lua5.4 luarocks libi2c-dev i2c-tools ghc \
  cabal-install zlib1g-dev
```

---

## 3. Build commands

All builds go through `build.py` at the repository root. Run `python3 build.py`
for a full build, or target a subset while iterating.

```sh
python3 build.py                              # Build all modules
python3 build.py --clean                      # Clean all artifacts
python3 build.py --module backend,frontend    # Build specific modules
python3 build.py --module backend --release   # Release mode (Rust only)
python3 build.py --list                       # List modules and their build commands
python3 build.py --verbose                    # Show detailed build output
```

Notes:

- Missing toolchains do not abort the run: `build.py` reports the modules it
  cannot build and continues with the rest.
- `--module` accepts a comma-separated list of module names, or `all`.
- `--release` only affects the Rust `backend` module.

---

## 4. Build diagnostics (required for every PR)

Each build writes a diagnostic bundle into the git-tracked `diagnostic/`
directory. The filenames are derived from the current commit so they stay stable
for that commit:

- `diagnostic/build-<commit-8-hex>.logd` — the encrypted build log (required)
- `diagnostic/build-<commit-8-hex>.json` — metadata: module results, and the
  password + `encryptly unpack` command needed to decrypt the `.logd`

`build.py` writes and **commits** these artifacts automatically. The
`Diagnostic build log` workflow (`.github/workflows/diagnostic-build-log.yml`)
fails any PR that does not add a new, non-empty `.logd` **and** `.json` under
`diagnostic/`. If the `.logd` exceeds the chunk limit it is split into
`build-<commit-8-hex>-partNNN.logd` chunks — commit all of them, and reassemble
with `cat` before unpacking.

Commit the diagnostic bundle on the same branch as your change:

```sh
python3 build.py
git status                       # diagnostic/build-<commit>.logd and .json appear
git add diagnostic/
git commit -m "Add build diagnostics for <commit>"
```

Maintainers may ask you to remove the diagnostic artifacts before merging; the
`pull_request_template.md` checklist has an option to request that.

---

## 5. Code style

Code style is defined by [`.editorconfig`](./.editorconfig) at the repository
root. Configure your editor to honour it (most editors do automatically) so
indentation, line endings, and trailing-whitespace rules stay consistent across
languages.

Language-specific conventions follow the ecosystem defaults:

- **Rust** (`backend/`) — `rustfmt` defaults; run `cargo fmt` before committing.
- **TypeScript / React** (`frontend/`) — 2-space indent; `tsc -b` must pass.
- **Go** (`market/`) — `gofmt`; tabs for indentation.
- **C / C++** (`frailbox/`, `frailbox/engine/`) — 4-space indent.
- **Java** (`compliance/`) — 4-space indent.
- **Lua, Ruby, Haskell** (`tools/`, `v2/`, `docs/openapi/`) — match the
  surrounding file.

Keep formatting-only changes out of functional PRs.

---

## 6. Pull request workflow

The flow is **fork > branch > commit > PR**:

1. **Fork** the repository (see section 1) and clone your fork.
2. **Branch** off an up-to-date `main` using a descriptive name:
   ```sh
   git checkout main
   git fetch upstream && git merge --ff-only upstream/main
   git checkout -b docs/short-description
   ```
3. **Commit** your change with a clear message. Keep the change scoped to a
   single purpose and avoid unrelated cleanup.
   ```sh
   git add <files>
   git commit -m "docs: describe the change"
   ```
4. **PR** — push the branch to your fork and open a pull request against
   `cuentaprueba244w-dotcom/zeroeye:main`:
   ```sh
   git push -u origin docs/short-description
   ```
   Then open the PR on GitHub. Fill in
   [`.github/pull_request_template.md`](./.github/pull_request_template.md) —
   the template is loaded automatically for new pull requests and asks for a
   summary, the list of changes, local test results, and the checklist.

### Before you open the PR

- [ ] The modules you touched build locally with `python3 build.py`.
- [ ] Tests pass locally.
- [ ] The new `diagnostic/build-<commit>.logd` and `.json` are committed.
- [ ] Documentation is updated if behaviour changed.
- [ ] Formatting matches `.editorconfig`.

---

## 7. Reporting issues

Use the issue templates under `.github/ISSUE_TEMPLATE/` (bug report or feature
request). Include a minimal reproduction, the exact commands you ran, and your
environment. Blank issues are also enabled.

---

## 8. Questions

Open an issue if anything in this guide is unclear or out of date — keeping it
accurate is part of contributing.
