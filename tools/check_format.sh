#!/bin/sh
set -eu

failures=0

fail() {
    printf '%s\n' "$1" >&2
    failures=$((failures + 1))
}

is_checked_file() {
    case "$1" in
        .editorconfig|Makefile|*.py|*.rs|*.ts|*.tsx|*.js|*.jsx|*.go|*.yaml|*.yml|*.json|*.md|*.c|*.h|*.cpp|*.hpp|*.java|*.lua|*.hs|*.rb|*.sh|*.pl|*.tf|*.toml|*.sql|*.html|*.css)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

if ! head -n 1 .editorconfig | grep -q '^# WARNING:'; then
    fail ".editorconfig: missing top warning comment"
fi

if ! grep -q '^root = true$' .editorconfig; then
    fail ".editorconfig: missing root = true"
fi

for file in $(git ls-files); do
    is_checked_file "$file" || continue
    [ -f "$file" ] || continue

    if LC_ALL=C grep -q "$(printf '\r')" "$file"; then
        fail "$file: contains CRLF line endings"
    fi

    if [ -s "$file" ] && [ "$(tail -c 1 "$file" | wc -l | tr -d ' ')" = "0" ]; then
        fail "$file: missing final newline"
    fi

    if grep -n '[[:blank:]]$' "$file" >/dev/null; then
        fail "$file: contains trailing whitespace"
    fi
done

if [ "$failures" -ne 0 ]; then
    printf 'format check failed: %s problem(s)\n' "$failures" >&2
    exit 1
fi

printf 'format check passed\n'
