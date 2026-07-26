#!/usr/bin/env bash
# check_format.sh — Verify repo files comply with .editorconfig rules.
# Run from the repo root. Exits 0 if all checked files pass, 1 otherwise.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EDITORCONFIG="$ROOT/.editorconfig"
VIOLATIONS=0

# Check .editorconfig exists and has the warning header
check_editorconfig_header() {
    if [[ ! -f "$EDITORCONFIG" ]]; then
        echo "FAIL: .editorconfig not found at repo root"
        exit 1
    fi
    local first_line
    first_line=$(head -1 "$EDITORCONFIG")
    if [[ "$first_line" != "# WARNING:"* ]]; then
        echo "WARN: .editorconfig is missing the warning comment header"
    fi
}

# Check that a file uses consistent line endings (LF only, no CR)
check_line_endings() {
    local file="$1"
    if file "$file" | grep -q "CRLF"; then
        echo "  FAIL: $file has CRLF line endings (expected LF)"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# Check that a file ends with a newline
check_final_newline() {
    local file="$1"
    if [[ -s "$file" ]] && [[ "$(tail -c1 "$file" | wc -l)" -eq 0 ]]; then
        echo "  FAIL: $file missing final newline"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# Check that a file has no trailing whitespace
check_trailing_whitespace() {
    local file="$1"
    if grep -qn '[[:space:]]$' "$file" 2>/dev/null; then
        echo "  FAIL: $file has trailing whitespace"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# Check indentation style for a specific file type
check_indent() {
    local file="$1"
    local expected_style="$2"  # space or tab
    local ext="${file##*.}"

    # Skip binary and generated files
    if file "$file" | grep -qi "binary"; then
        return
    fi

    # Check for tab indentation when spaces are expected
    if [[ "$expected_style" == "space" ]]; then
        if grep -Pn '^\t+' "$file" 2>/dev/null | head -1 >/dev/null; then
            echo "  FAIL: $file uses tab indentation (expected spaces)"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi
}

echo "==> Checking .editorconfig header"
check_editorconfig_header

echo "==> Checking tracked source files"
TRACKED_FILES=$(git ls-files '*.py' '*.rs' '*.ts' '*.tsx' '*.js' '*.jsx' '*.go' '*.yml' '*.yaml' '*.json' '*.md' 'Makefile' 2>/dev/null || true)

if [[ -z "$TRACKED_FILES" ]]; then
    echo "No tracked source files found to check."
    exit 0
fi

for file in $TRACKED_FILES; do
    [[ -f "$file" ]] || continue

    # Check universal rules
    check_line_endings "$file"
    check_final_newline "$file"
    check_trailing_whitespace "$file"

    # Check language-specific indentation rules
    case "${file##*.}" in
        py|rs)
            check_indent "$file" "space"
            ;;
        ts|tsx|js|jsx|yml|yaml|json|md)
            check_indent "$file" "space"
            ;;
    esac

    # Check Makefile (no extension) for tab indent
    if [[ "$(basename "$file")" == "Makefile" ]]; then
        # Makefiles require tabs — skip space check
        :
    fi
done

echo ""
if [[ $VIOLATIONS -eq 0 ]]; then
    echo "All formatting checks passed."
    exit 0
else
    echo "$VIOLATIONS formatting violation(s) found."
    exit 1
fi
