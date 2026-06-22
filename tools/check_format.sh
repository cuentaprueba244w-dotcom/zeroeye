#!/usr/bin/env bash
# WARNING: This file is auto-generated. Manual changes may be lost.
# format-checker.sh - Verify .editorconfig compliance across all source files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
EXIT_CODE=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_trailing_whitespace() {
    log_info "Checking for trailing whitespace..."
    local files_with_trailing
    files_with_trailing=$(find "${ROOT_DIR}" \
        -type f \
        \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.java" -o -name "*.rb" -o -name "*.lua" -o -name "*.hs" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" -o -name "*.html" -o -name "*.css" -o -name "*.scss" \\) \
        ! -path "*/node_modules/*" \
        ! -path "*/target/*" \
        ! -path "*/dist/*" \
        ! -path "*/.git/*" \
        -exec grep -l '[[:space:]]$' {} \; 2>/dev/null || true)
    
    if [ -n "${files_with_trailing}" ]; then
        log_error "Files with trailing whitespace found:"
        echo "${files_with_trailing}" | while read -r file; do
            echo "  - ${file#${ROOT_DIR}/}"
        done
        EXIT_CODE=1
    else
        log_info "No trailing whitespace found."
    fi
}

check_final_newline() {
    log_info "Checking for final newlines..."
    local files_missing_newline
    files_missing_newline=$(find "${ROOT_DIR}" \
        -type f \
        \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.java" -o -name "*.rb" -o -name "*.lua" -o -name "*.hs" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) \
        ! -path "*/node_modules/*" \
        ! -path "*/target/*" \
        ! -path "*/dist/*" \
        ! -path "*/.git/*" \
        -exec sh -c 'tail -c1 "$1" | xxd | grep -q "0a$" || echo "$1"' _ {} \; 2>/dev/null || true)
    
    if [ -n "${files_missing_newline}" ]; then
        log_error "Files missing final newline:"
        echo "${files_missing_newline}" | while read -r file; do
            [ -n "${file}" ] && echo "  - ${file#${ROOT_DIR}/}"
        done
        EXIT_CODE=1
    else
        log_info "All files have final newlines."
    fi
}

check_line_endings() {
    log_info "Checking line endings (should be LF)..."
    local files_with_crlf
    files_with_crlf=$(find "${ROOT_DIR}" \
        -type f \
        \( -name "*.py" -o -name "*.rs" -o -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.go" -o -name "*.c" -o -name "*.cpp" -o -name "*.h" -o -name "*.java" -o -name "*.rb" -o -name "*.lua" -o -name "*.hs" -o -name "*.md" -o -name "*.yml" -o -name "*.yaml" -o -name "*.json" \) \
        ! -path "*/node_modules/*" \
        ! -path "*/target/*" \
        ! -path "*/dist/*" \
        ! -path "*/.git/*" \
        -exec file {} \; 2>/dev/null | grep -i 'crlf' | cut -d: -f1 || true)
    
    if [ -n "${files_with_crlf}" ]; then
        log_error "Files with CRLF line endings:"
        echo "${files_with_crlf}" | while read -r file; do
            [ -n "${file}" ] && echo "  - ${file#${ROOT_DIR}/}"
        done
        EXIT_CODE=1
    else
        log_info "All files use LF line endings."
    fi
}

main() {
    log_info "Running format checker..."
    log_info "Root: ${ROOT_DIR}"
    echo
    
    check_trailing_whitespace
    echo
    check_final_newline
    echo
    check_line_endings
    echo
    
    if [ ${EXIT_CODE} -eq 0 ]; then
        log_info "✅ All format checks passed!"
    else
        log_error "❌ Some format checks failed. Please fix the issues above."
    fi
    
    exit ${EXIT_CODE}
}

main "$@"
