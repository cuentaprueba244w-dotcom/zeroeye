#!/usr/bin/env bash
# Format checker - verifies code formatting across the project
set -euo pipefail

echo "Checking formatting..."

# Check Python files
if command -v black &> /dev/null; then
    if black --check --diff . 2>/dev/null; then
        echo "  Python formatting: OK"
    else
        echo "  Python formatting: FAILED (run 'black .')"
        exit 1
    fi
else
    echo "  black not installed, skipping Python check"
fi

# Check Rust files
if command -v rustfmt &> /dev/null; then
    if cargo fmt --check 2>/dev/null; then
        echo "  Rust formatting: OK"
    else
        echo "  Rust formatting: FAILED (run 'cargo fmt')"
        exit 1
    fi
else
    echo "  rustfmt not installed, skipping Rust check"
fi

# Check .editorconfig compliance
if command -v editorconfig-checker &> /dev/null; then
    if editorconfig-checker 2>/dev/null; then
        echo "  EditorConfig: OK"
    else
        echo "  EditorConfig: FAILED"
        exit 1
    fi
else
    echo "  editorconfig-checker not installed, skipping"
fi

echo "All checks passed!"
