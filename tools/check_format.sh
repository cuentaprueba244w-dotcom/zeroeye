#!/bin/bash
# WARNING: This format checker enforces .editorconfig rules.
# Run before committing.

set -euo pipefail

echo "=== Format Checker ==="
echo "Checking .editorconfig compliance..."
echo ""

HAS_ERRORS=0

# Function to check files with a specific extension
check_ext() {
    local ext="$1"
    local name="$2"
    local files
    files=$(find . -name "$ext" -not -path "./.git/*" -not -path "./node_modules/*" -not -path "./target/*" 2>/dev/null || true)
    local count
    count=$(echo "$files" | grep -c . || true)
    if [ "$count" -gt 0 ]; then
        echo "  ✓ $name: $count file(s)"
    fi
}

# Report language coverage
echo "Languages found in repository:"
check_ext "*.py" "Python"
check_ext "*.rs" "Rust"
check_ext "*.ts" "TypeScript"
check_ext "*.tsx" "TypeScript JSX"
check_ext "*.js" "JavaScript"
check_ext "*.go" "Go"
check_ext "*.c" "C"
check_ext "*.h" "C Header"
check_ext "*.cpp" "C++"
check_ext "*.hpp" "C++ Header"
check_ext "*.java" "Java"
check_ext "*.rb" "Ruby"
check_ext "*.lua" "Lua"
check_ext "*.hs" "Haskell"
check_ext "*.yml" "YAML"
check_ext "*.yaml" "YAML"
check_ext "*.json" "JSON"
check_ext "*.toml" "TOML"
check_ext "*.md" "Markdown"
check_ext "*.sh" "Shell"
echo ""

# Check for trailing whitespace
echo "Checking trailing whitespace..."
BAD_WS=$(grep -rIn '[[:space:]]$' --include="*.py" --include="*.rs" --include="*.ts" \
    --include="*.js" --include="*.go" --include="*.c" --include="*.h" --include="*.cpp" \
    --include="*.java" --include="*.rb" --include="*.lua" --include="*.hs" \
    . 2>/dev/null | grep -v '.git/' | head -20 || true)
if [ -n "$BAD_WS" ]; then
    echo "  ✗ Trailing whitespace found:"
    echo "$BAD_WS"
    HAS_ERRORS=1
else
    echo "  ✓ No trailing whitespace"
fi

# Check for missing final newline
echo "Checking final newlines..."
for f in $(find . -type f -name "*.py" -o -name "*.rs" -o -name "*.go" -o -name "*.ts" \
    -o -name "*.js" -o -name "*.c" -o -name "*.h" -o -name "*.cpp" -o -name "*.java" \
    -o -name "*.rb" -o -name "*.lua" -o -name "*.hs" -o -name "*.sh" -o -name "*.yml" \
    -o -name "*.yaml" -o -name "*.json" -o -name "*.toml" 2>/dev/null | grep -v '.git/' | grep -v 'node_modules/' | grep -v 'target/' || true); do
    if [ -s "$f" ] && [ "$(tail -c 1 "$f" | wc -l)" -eq 0 ]; then
        echo "  ✗ Missing final newline: $f"
        HAS_ERRORS=1
    fi
done

echo ""
if [ "$HAS_ERRORS" -eq 0 ]; then
    echo "✓ All files pass format checks."
else
    echo "✗ Some files have formatting issues. Fix them before committing."
fi

exit $HAS_ERRORS
