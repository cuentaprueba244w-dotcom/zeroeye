# Contributing

Thanks for helping improve Tent of Trials. Keep changes focused, verify the
modules you touch, and include enough build evidence for reviewers to reproduce
your work.

## Clone and Branch

```bash
git clone https://github.com/lobster-trap/TentOfTrials.git
cd TentOfTrials
git switch -c your-branch-name
```

If you do not have write access, fork the repository first, clone your fork, and
keep the upstream repository available as a remote:

```bash
git remote add upstream https://github.com/lobster-trap/TentOfTrials.git
git fetch upstream
```

## Local Setup

Install the tools for the modules you plan to edit. The repository currently
contains Rust, TypeScript/React, Go, C, C++, Java, Ruby, Lua, and Haskell
components, plus Python repo tooling.

For Python repo tooling:

```bash
sudo apt update
sudo apt install -y python3
```

For backend Rust work:

```bash
sudo apt install -y build-essential pkg-config curl protobuf-compiler libssl-dev
curl https://sh.rustup.rs -sSf | sh -s -- -y
source "$HOME/.cargo/env"
cargo fetch
```

For frontend TypeScript/React work:

```bash
sudo apt install -y curl ca-certificates gnupg
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
npm install --prefix frontend
```

For Go market services:

```bash
sudo apt install -y golang-go
(cd market && go mod download)
```

For C/C++, Java, Ruby, Lua, and Haskell modules, install the dependencies listed
in `README.md` for the module you are changing.

## Build Commands

Use the top-level build runner for normal verification:

```bash
python3 build.py
```

Useful variants:

```bash
python3 build.py --list
python3 build.py --module backend,frontend
python3 build.py --release
python3 build.py --clean
```

Module-specific commands are also useful while iterating:

```bash
(cd backend && cargo build)
(cd frontend && npm run build)
(cd market && go build -o market .)
(cd frailbox && make)
(cd compliance && javac -d build ComplianceAuditor.java)
```

Every PR should describe the exact commands run and their results. When
`python3 build.py` generates diagnostic files under `diagnostic/`, include the
required diagnostic artifacts unless a maintainer asks for them to be removed.

## Code Style

Follow the root `.editorconfig` for indentation, line endings, and charset. If
your editor supports EditorConfig, enable it before editing. In general:

- Python and Rust use four spaces.
- TypeScript, JavaScript, YAML, JSON, and Markdown use two spaces.
- Go and Makefiles use tabs.

Keep generated artifacts out of commits unless they are explicitly required for
review, such as the diagnostic build log mentioned above.

## Pull Request Workflow

1. Fork the repository if needed.
2. Create a focused branch from the current target branch.
3. Make the smallest coherent change that satisfies the issue or bug.
4. Run relevant tests and build commands locally.
5. Commit with a concise message.
6. Push your branch and open a pull request.

Use the repository pull request template:
`.github/pull_request_template.md`.

In the PR:

- Link the issue being fixed.
- Fill in the Summary, Changes, Testing, and Checklist sections.
- Include generated diagnostic artifacts when required.
- Keep unrelated cleanup and formatting out of the branch.
