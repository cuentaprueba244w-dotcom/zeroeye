#!/usr/bin/env bash
#
# check_format.sh - Format checker for Tent of Trials
#
# Verifies that files across the repository comply with the formatting
# rules defined in .editorconfig. Checks trailing whitespace, final
# newlines, line endings (LF), and indentation consistency.
#
# Usage:
#   bash tools/check_format.sh          # Check all files
#   bash tools/check_format.sh --fix    # Attempt automatic fixes
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EDITORCONFIG="$ROOT_DIR/.editorconfig"
FIX_MODE=false
EXIT_CODE=0

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --fix)
            FIX_MODE=true
            ;;
        -h|--help)
            echo "Usage: bash tools/check_format.sh [--fix]"
            echo ""
            echo "  --fix   Attempt to fix formatting issues automatically"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown argument: $arg"
            exit 1
            ;;
    esac
done

if [[ ! -f "$EDITORCONFIG" ]]; then
    echo "ERROR: .editorconfig not found at $EDITORCONFIG"
    exit 1
fi

echo "Checking formatting against .editorconfig..."
echo "Root: $ROOT_DIR"
echo ""

# Function: check trailing whitespace
check_trailing_whitespace() {
    local file="$1"
    local errors=0

    # Skip binary files
    if file "$file" | grep -qi "binary"; then
        return 0
    fi

    if grep -n '[[:space:]]$' "$file" 2>/dev/null; then
        errors=$((errors + 1))
        if [[ "$FIX_MODE" == "true" ]]; then
            sed -i 's/[[:space:]]*$//' "$file"
            echo "  FIXED: $file"
        fi
    fi

    return $errors
}

# Function: check final newline
check_final_newline() {
    local file="$1"

    if [[ ! -s "$file" ]]; then
        return 0
    fi

    # Check if file ends with a newline
    if [[ -n "$(tail -c 1 "$file" 2>/dev/null)" ]]; then
        if [[ "$FIX_MODE" == "true" ]]; then
            echo "" >> "$file"
            echo "  FIXED: Added final newline to $file"
        else
            echo "  FAIL: $file - missing final newline"
            return 1
        fi
    fi

    return 0
}

# Function: check for CRLF line endings
check_line_endings() {
    local file="$1"

    if file "$file" | grep -qi "binary"; then
        return 0
    fi

    if grep -rIl $'\r$' "$file" 2>/dev/null; then
        if [[ "$FIX_MODE" == "true" ]]; then
            sed -i 's/\r$//' "$file"
            echo "  FIXED: Converted CRLF to LF in $file"
        else
            echo "  FAIL: $file - contains CRLF line endings (expected LF)"
            return 1
        fi
    fi

    return 0
}

# Function: check indentation for Python files
check_python_indent() {
    local file="$1"
    local errors=0

    # Check for tab characters in Python files (should be spaces)
    if grep -nP '\t' "$file" 2>/dev/null | head -5; then
        errors=$((errors + 1))
        if [[ "$FIX_MODE" == "true" ]]; then
            echo "  WARNING: Tab characters found in Python file $file (manual review needed)"
        fi
    fi

    return $errors
}

# Function: check indentation for YAML/JSON files
check_yaml_json_indent() {
    local file="$1"
    local errors=0

    # Check for tab characters in YAML/JSON files (should be spaces)
    if grep -nP '\t' "$file" 2>/dev/null | head -5; then
        errors=$((errors + 1))
        if [[ "$FIX_MODE" == "true" ]]; then
            sed -i 's/\t/  /g' "$file"
            echo "  FIXED: Replaced tabs with spaces in $file"
        fi
    fi

    return $errors
}

# Function: check indentation for Makefiles (should use tabs)
check_makefile_indent() {
    local file="$1"
    local errors=0

    # Check for space-indented recipe lines in Makefile (should be tabs)
    while IFS=: read -r linenum line; do
        if [[ "$line" =~ ^[[:space:]]*[a-zA-Z] ]] && ! [[ "$line" =~ ^$(printf '\t') ]]; then
            echo "  WARN: $file:$linenum - recipe line may use spaces instead of tab"
            errors=$((errors + 1))
        fi
    done < <(grep -n '' "$file" 2>/dev/null)

    return $errors
}

# Main check logic
echo "=== Trailing Whitespace Check ==="
TW_ERRORS=0
while IFS= read -r -d '' file; do
    if ! check_trailing_whitespace "$file"; then
        TW_ERRORS=$((TW_ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" \
    -type f \
    \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" \
       -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.java" \
       -o -name "*.c" -o -name "*.cpp" -o -name "*.hpp" -o -name "*.h" \
       -o -name "*.lua" -o -name "*.rb" -o -name "*.hs" \
       -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \
       -o -name "*.md" -o -name "*.sh" -o -name "Makefile" \
       -o -name "*.toml" -o -name "*.cfg" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/target/*" \
    -not -path "*/.git/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -print0 2>/dev/null)
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  Trailing whitespace issues found: $TW_ERRORS"
fi

echo ""
echo "=== Final Newline Check ==="
NL_ERRORS=0
while IFS= read -r -d '' file; do
    if ! check_final_newline "$file"; then
        NL_ERRORS=$((NL_ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" \
    -type f \
    \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" \
       -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.java" \
       -o -name "*.c" -o -name "*.cpp" -o -name "*.hpp" -o -name "*.h" \
       -o -name "*.lua" -o -name "*.rb" -o -name "*.hs" \
       -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \
       -o -name "*.md" -o -name "*.sh" -o -name "Makefile" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/target/*" \
    -not -path "*/.git/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -print0 2>/dev/null)
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  Final newline issues found: $NL_ERRORS"
fi

echo ""
echo "=== Line Ending Check (LF vs CRLF) ==="
LE_ERRORS=0
while IFS= read -r -d '' file; do
    if ! check_line_endings "$file"; then
        LE_ERRORS=$((LE_ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" \
    -type f \
    \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" \
       -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.java" \
       -o -name "*.c" -o -name "*.cpp" -o -name "*.hpp" -o -name "*.h" \
       -o -name "*.lua" -o -name "*.rb" -o -name "*.hs" \
       -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \
       -o -name "*.md" -o -name "*.sh" -o -name "Makefile" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/target/*" \
    -not -path "*/.git/*" \
    -not -path "*/dist/*" \
    -not -path "*/build/*" \
    -print0 2>/dev/null)
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  Line ending issues found: $LE_ERRORS"
fi

echo ""
echo "=== Python Indentation Check ==="
PY_INDENT_ERRORS=0
while IFS= read -r -d '' file; do
    if ! check_python_indent "$file"; then
        PY_INDENT_ERRORS=$((PY_INDENT_ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" -type f -name "*.py" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/target/*" \
    -print0 2>/dev/null)
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  Python indentation issues found: $PY_INDENT_ERRORS"
fi

echo ""
echo "=== YAML/JSON Indentation Check ==="
YJ_INDENT_ERRORS=0
while IFS= read -r -d '' file; do
    if ! check_yaml_json_indent "$file"; then
        YJ_INDENT_ERRORS=$((YJ_INDENT_ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" \
    -type f \
    \( -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/target/*" \
    -not -path "*/dist/*" \
    -print0 2>/dev/null)
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  YAML/JSON indentation issues found: $YJ_INDENT_ERRORS"
fi

echo ""
echo "=== Makefile Indentation Check ==="
MK_INDENT_ERRORS=0
for mkfile in $(find "$ROOT_DIR" -type f -name "Makefile" \
    -not -path "*/.git/*" \
    -not -path "*/node_modules/*" \
    2>/dev/null); do
    if ! check_makefile_indent "$mkfile"; then
        MK_INDENT_ERRORS=$((MK_INDENT_ERRORS + 1))
    fi
done
if [[ "$FIX_MODE" != "true" ]]; then
    echo "  Makefile indentation issues found: $MK_INDENT_ERRORS"
fi

echo ""
echo "=== Summary ==="

TOTAL_ERRORS=$((TW_ERRORS + NL_ERRORS + LE_ERRORS + PY_INDENT_ERRORS + YJ_INDENT_ERRORS + MK_INDENT_ERRORS))

if [[ "$FIX_MODE" == "true" ]]; then
    echo "Fix mode completed. Re-run without --fix to verify."
    exit 0
fi

if [[ "$TOTAL_ERRORS" -eq 0 ]]; then
    echo "All formatting checks passed."
    exit 0
else
    echo "Total formatting issues found: $TOTAL_ERRORS"
    echo ""
    echo "Run 'bash tools/check_format.sh --fix' to attempt automatic fixes."
    exit 1
fi
