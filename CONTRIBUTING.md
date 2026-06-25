# Contributing to Tent of Trials

Thanks for helping with this repository. Tent of Trials is a polyglot trading and
risk platform, so the best contributions are narrow, well-tested, and honest
about which toolchains were available locally. If your change touches only one
module, keep the PR scoped to that module.

## Local setup

Clone the repository and install the toolchains for the modules you plan to
change:

```bash
git clone https://github.com/cuentaprueba244w-dotcom/zeroeye.git
cd zeroeye
python3 --version
```

For a full checkout, the README lists the combined Ubuntu package install
command. For focused work, install only the relevant module toolchain:

- Backend: Rust, `pkg-config`, `protobuf-compiler`, and OpenSSL headers.
- Frontend: Node.js 22 and npm.
- Market: Go.
- Frailbox: C build tools, `make`, and Linux headers.
- Engine: C++ build tools and CMake.
- Compliance: OpenJDK 21.
- v2 market stream: Ruby, Redis, and required gems.
- Scanner/OpenAPI tools: Lua, LuaRocks, GHC, and Cabal as needed.

## Build commands by module

Use `build.py` for the repository-level build because it creates the diagnostic
bundle reviewers expect:

```bash
python3 build.py
python3 build.py --module backend
python3 build.py --module frontend
python3 build.py --module market
python3 build.py --module backend,frontend
python3 build.py --release
```

Focused module commands are useful before running the repository build:

```bash
# Backend
cd backend
cargo test
cargo fmt --check

# Frontend
cd frontend
npm install
npm test
npm run build

# Market
cd market
go test ./...

# Python tooling
python3 -m compileall tools build.py
```

If a local machine lacks a required compiler or runtime, still run the closest
focused command and explain the blocker in the PR. Do not mark unavailable
validation as passing.

## Required diagnostic workflow

Before opening a PR, run:

```bash
python3 build.py
```

The build writes diagnostic files under `diagnostic/`, normally named like
`build-<commit>.logd` with a matching JSON metadata file. Include the generated
diagnostic artifacts in the PR branch when the bounty or reviewer asks for them.
If the diagnostic contains environment details that should not be merged, check
the template box requesting removal before merge.

## Pull request workflow

1. Fork the repository.
2. Create a descriptive branch, for example `fix/backend-contract-tests`.
3. Keep the diff focused on the issue you are solving.
4. Run the focused validation command for the touched module.
5. Run `python3 build.py` and include generated diagnostics when required.
6. Open a PR using `.github/pull_request_template.md`.
7. Link the issue in the PR body with `Fixes #<issue-number>` when appropriate.

The PR template requires:

- a short summary,
- notable changes,
- exact commands run and their results,
- checklist status,
- whether diagnostic artifacts should be removed before merge.

## Style and formatting

There is currently no repository-level `.editorconfig`. Until one is added, use
the conventions already present in the touched module:

- Python: 4-space indentation.
- Rust: `rustfmt`.
- TypeScript/JavaScript/JSON/YAML/Markdown: 2-space indentation.
- Go: `gofmt`.
- Makefiles: tabs.

Avoid unrelated formatting sweeps. They make review harder and can hide the
actual fix.

## Bounty-specific notes

Many issues in this repository require proof that the work was tested. Include
the exact command output or diagnostic artifact reference in the PR body. If a
bounty asks for build diagnostics and your environment cannot generate them,
state that clearly instead of reusing stale artifacts.
