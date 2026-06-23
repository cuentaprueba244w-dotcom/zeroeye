#!/usr/bin/env bash
set -euo pipefail

check_file() {
    local file="$1"
    local errors=0
    if grep -n "[[:space:]]$" "$file" 2>/dev/null; then
        echo "ERROR: Trailing whitespace in $file"
        errors=$((errors + 1))
    fi
    if [ -s "$file" ] && [ "$(tail -c 1 "$file" | wc -l)" -eq 0 ]; then
        echo "ERROR: Missing final newline in $file"
        errors=$((errors + 1))
    fi
    return $errors
}

all_passed=0
while IFS= read -r -d "" file; do
    check_file "$file" || all_passed=$((all_passed + 1))
done < <(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.rs" -o -name "*.go" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/.git/*" ! -path "*/vendor/*" -print0)

if [ "$all_passed" -eq 0 ]; then
    echo "Format check passed."
else
    echo "Format check found $all_passed file(s) with issues."
    exit 1
fi
