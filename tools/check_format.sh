#!/usr/bin/env bash
set -e

# Download and run editorconfig-checker to verify formatting
echo "Verifying .editorconfig compliance across all languages..."

if ! command -v editorconfig-checker &> /dev/null; then
    echo "Downloading editorconfig-checker..."
    curl -sL https://github.com/editorconfig-checker/editorconfig-checker/releases/download/2.7.2/ec-linux-amd64.tar.gz | tar xz
    chmod +x bin/ec-linux-amd64
    CHECKER="./bin/ec-linux-amd64"
else
    CHECKER="editorconfig-checker"
fi

$CHECKER -exclude '.*.tsbuildinfo|Cargo\.lock|\.git/|node_modules/|package-lock\.json' -disable-indent-size
echo "Format check passed successfully!"
