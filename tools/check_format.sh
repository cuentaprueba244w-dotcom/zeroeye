#!/usr/bin/env bash
# tools/check_format.sh - Verify .editorconfig compliance across the polyglot codebase.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EDITORCONFIG="$REPO_ROOT/.editorconfig"

if [[ ! -f "$EDITORCONFIG" ]]; then
  echo "ERROR: .editorconfig not found at $EDITORCONFIG"
  exit 1
fi

echo "Checking .editorconfig formatting compliance..."
errors=0

while IFS= read -r -d '' file; do
  if grep -Pn '\t' "$file" >/dev/null 2>&1; then
    echo "  FAIL: $file contains tabs (expected 4-space indent)"
    errors=$((errors + 1))
  fi
done < <(find "$REPO_ROOT" -name '*.py' -not -path '*/node_modules/*' -not -path '*/.git/*' -print0)

while IFS= read -r -d '' file; do
  if grep -Pn '\t' "$file" >/dev/null 2>&1; then
    echo "  FAIL: $file contains tabs (expected 4-space indent)"
    errors=$((errors + 1))
  fi
done < <(find "$REPO_ROOT" -name '*.rs' -not -path '*/.git/*' -print0)

while IFS= read -r -d '' file; do
  if grep -Pn '^\t' "$file" >/dev/null 2>&1; then
    echo "  FAIL: $file starts lines with tabs (expected 2-space indent)"
    errors=$((errors + 1))
  fi
done < <(find "$REPO_ROOT" \( -name '*.ts' -o -name '*.js' -o -name '*.tsx' -o -name '*.jsx' \) -not -path '*/node_modules/*' -not -path '*/.git/*' -print0)

while IFS= read -r -d '' file; do
  if grep -Pn '^    ' "$file" >/dev/null 2>&1; then
    echo "  WARN: $file starts lines with spaces (expected tab indent for Go)"
  fi
done < <(find "$REPO_ROOT" -name '*.go' -not -path '*/.git/*' -print0)

while IFS= read -r -d '' file; do
  if grep -Pn '\t' "$file" >/dev/null 2>&1; then
    echo "  FAIL: $file contains tabs (expected 2-space indent)"
    errors=$((errors + 1))
  fi
done < <(find "$REPO_ROOT" \( -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.md' \) -not -path '*/node_modules/*' -not -path '*/.git/*' -print0)

if grep -Pn '\r$' "$EDITORCONFIG" >/dev/null 2>&1; then
  echo "  FAIL: .editorconfig contains CRLF line endings (expected LF)"
  errors=$((errors + 1))
fi

echo ""
if [[ $errors -eq 0 ]]; then
  echo "All formatting checks passed."
  exit 0
else
  echo "$errors formatting issue(s) found."
  exit 1
fi
