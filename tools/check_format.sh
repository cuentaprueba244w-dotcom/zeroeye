#!/bin/bash
# Zeroeye Format Checker
# Verifies that all source files comply with .editorconfig rules.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0
CHECKED=0

# File extensions to check (from .editorconfig)
EXTENSIONS=("c" "cpp" "h" "hpp" "rs" "py" "go" "hs" "lua" "yml" "yaml" "json" "md" "ts" "tsx" "sh")

echo "=== Zeroeye Format Checker ==="
echo "Checking compliance with .editorconfig"
echo ""

check_file() {
    local file="$1"
    local ext="${file##*.}"

    # Skip if not a tracked extension
    local valid=0
    for e in "${EXTENSIONS[@]}"; do
        if [ "$ext" = "$e" ]; then valid=1; break; fi
    done
    if [ "$valid" -eq 0 ]; then return; fi

    CHECKED=$((CHECKED + 1))
    local file_errors=0

    # Check trailing whitespace (not for .md)
    if [ "$ext" != "md" ]; then
        if grep -q '[[:space:]]$' "$file" 2>/dev/null; then
            echo "  [FAIL] $file: trailing whitespace"
            file_errors=$((file_errors + 1))
        fi
    fi

    # Check missing final newline
    if [ -s "$file" ] && [ "$(tail -c 1 "$file")" != "" ]; then
        echo "  [FAIL] $file: missing final newline"
        file_errors=$((file_errors + 1))
    fi

    # Check tab usage in space-indented files
    case "$ext" in
        c|cpp|h|hpp|rs|py|hs|lua|yml|yaml|json|md|ts|tsx|sh)
            if grep -lP '^\t' "$file" 2>/dev/null > /dev/null; then
                echo "  [FAIL] $file: uses tabs for indentation (expects spaces)"
                file_errors=$((file_errors + 1))
            fi
            ;;
    esac

    if [ "$file_errors" -gt 0 ]; then
        ERRORS=$((ERRORS + file_errors))
        return 1
    fi
    return 0
}

# Traverse repository
while IFS= read -r -d '' file; do
    # Skip .git and generated/third-party dirs
    case "$file" in
        */.git/*|*/node_modules/*|*/__pycache__/*|*/diagnostic/*|*/target/*|*/dist/*) continue ;;
    esac
    check_file "$file"
done < <(find . -type f -print0)

echo ""
echo "=== Summary ==="
echo "Files checked: $CHECKED"
echo "Format errors: $ERRORS"

if [ "$ERRORS" -gt 0 ]; then
    echo "FAILED: $ERRORS format violation(s) found."
    exit 1
else
    echo "PASSED: All files comply with .editorconfig."
    exit 0
fi
