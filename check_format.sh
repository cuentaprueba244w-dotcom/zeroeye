#!/bin/bash
# Format checker that enforces .editorconfig rules across the repo

set -e

echo "Running format checks..."
ERRORS=0

# Exclude .git and build directories
FILES=$(find . -type f -not -path "*/\.git/*" -not -path "*/node_modules/*" -not -path "*/target/*" -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/__pycache__/*")

for file in $FILES; do
    # Check for trailing whitespace (except in markdown)
    if [[ "$file" != *.md ]]; then
        if grep -q "[[:blank:]]$" "$file"; then
            echo "Error: Trailing whitespace found in $file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
    
    # Check for EOF newline
    if [ -s "$file" ]; then
        if [ "$(tail -c 1 "$file" | wc -l)" -eq 0 ]; then
            echo "Error: No newline at end of file in $file"
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo "Format check failed with $ERRORS errors."
    exit 1
else
    echo "Format check passed!"
    exit 0
fi
