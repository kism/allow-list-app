#!/usr/bin/env bash

set -euo pipefail

function print_heading() {
    echo
    echo "=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-="
    echo "$1 >>>"
}

print_heading "Running tests with coverage measurement..."
coverage run

print_heading "Generating HTML coverage report..."
coverage html

print_heading "Generating coverage report in terminal..."
coverage report

print_heading "View HTML coverage report"
echo 'python -m http.server -b 127.0.0.1 8000 -d htmlcov'
