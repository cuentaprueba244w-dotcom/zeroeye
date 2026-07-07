#!/bin/bash
# Format checker script — verifies .editorconfig compliance across languages
# Usage: ./tools/check_format.sh
# Returns 0 if all checks pass, non-zero otherwise.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ERRORS=0

echo "=== Format Compliance Checker ==="
echo ""

# Check .editorconfig exists
if [ ! -f "$ROOT_DIR/.editorconfig" ]; then
    echo "FAIL: .editorconfig not found in project root"
    ERRORS=$((ERRORS + 1))
else
    echo "PASS: .editorconfig exists"
fi

# Check for trailing whitespace in non-excluded files
echo ""
echo "--- Trailing Whitespace Check ---"
if grep -rI --include="*.py" --include="*.rs" --include="*.go" --include="*.ts" \
    --include="*.tsx" --include="*.js" --include="*.jsx" --include="*.java" \
    --include="*.sol" --include="*.sh" --include="*.toml" --include="*.json" \
    --include="*.yaml" --include="*.yml" --include="*.html" --include="*.css" \
    --include="*.lua" \
    '[[:space:]]$' "$ROOT_DIR" \
    --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=target 2>/dev/null | grep -v "Binary file" || true
then
    echo "WARNING: Files with trailing whitespace found (see above)"
    ERRORS=$((ERRORS + 1))
else
    echo "PASS: No trailing whitespace found"
fi

# Check for missing final newline
echo ""
echo "--- Final Newline Check ---"
while IFS= read -r -d '' file; do
    if [ -s "$file" ] && [ "$(tail -c 1 "$file" | wc -l)" -eq 0 ]; then
        echo "FAIL: Missing final newline: $file"
        ERRORS=$((ERRORS + 1))
    fi
done < <(find "$ROOT_DIR" -type f \( -name "*.py" -o -name "*.rs" -o -name "*.go" \
    -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
    -o -name "*.java" -o -name "*.sol" -o -name "*.sh" -o -name "*.toml" \
    -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.html" \
    -o -name "*.css" -o -name "*.lua" \) \
    -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/target/*" -print0)

if [ $ERRORS -eq 0 ]; then
    echo "PASS: All files have final newlines"
fi

# Check for CRLF line endings
echo ""
echo "--- Line Ending Check (CRLF) ---"
if find "$ROOT_DIR" -type f \( -name "*.py" -o -name "*.rs" -o -name "*.go" \
    -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \
    -o -name "*.java" -o -name "*.sol" -o -name "*.sh" -o -name "*.toml" \
    -o -name "*.json" -o -name "*.yaml" -o -name "*.yml" -o -name "*.html" \
    -o -name "*.css" -o -name "*.lua" \) \
    -not -path "*/.git/*" -not -path "*/node_modules/*" -not -path "*/target/*" \
    -exec grep -l $'\r' {} \; 2>/dev/null | grep -v "Binary file" || true
then
    echo "FAIL: CRLF line endings found (see above)"
    ERRORS=$((ERRORS + 1))
else
    echo "PASS: No CRLF line endings"
fi

echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "All format checks passed!"
    exit 0
else
    echo "$ERRORS check(s) failed"
    exit 1
fi