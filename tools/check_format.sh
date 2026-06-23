#!/usr/bin/env bash
set -euo pipefail

check_file() {
    local file="$1"
    local errors=0
    if grep -n "[[:space:]]$" "$file" 2>/dev/null; then
        echo "Trailing whitespace: $file"
        errors=1
    fi
    if [ -s "$file" ] && [ "$(tail -c 1 "$file" | wc -l)" -eq 0 ]; then
        echo "Missing final newline: $file"
        errors=1
    fi
    return $errors
}

fail=0
while IFS= read -r -d "" f; do
    check_file "$f" || fail=1
done < <(find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.rs" -o -name "*.go" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/.git/*" ! -path "*/vendor/*" -print0)
[ "$fail" -eq 0 ] && echo "All files comply." || echo "Some files need formatting."
exit $fail
