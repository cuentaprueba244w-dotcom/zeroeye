#!/bin/bash
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

find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.rs" -o -name "*.go" \) ! -path "*/node_modules/*" ! -path "*/target/*" ! -path "*/.git/*" | while read -r file; do
    check_file "$file"
done
echo "Format check complete."
