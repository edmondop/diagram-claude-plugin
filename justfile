# diagram-claude-plugin task runner

default:
    @just --list

# Run ruff linter on all Python scripts
lint:
    uvx ruff check scripts/

# Check Python formatting
format-check:
    uvx ruff format --check scripts/

# Auto-format Python scripts
format:
    uvx ruff format scripts/

# Type-check Python scripts
typecheck:
    uvx pyrefly check scripts/

# Lint all Markdown files
markdown-lint:
    npx markdownlint-cli2 "**/*.md" "#node_modules"

# Smoke-test: run every script and verify SVG output
test:
    #!/usr/bin/env bash
    set -euo pipefail
    cd scripts
    rm -rf output
    failures=0
    for script in *.py; do
        echo "Running $script..."
        if uv run "$script"; then
            echo "  OK"
        else
            echo "  FAILED"
            failures=$((failures + 1))
        fi
    done
    echo ""
    echo "Output files:"
    ls -la output/ 2>/dev/null || echo "  (no output directory)"
    if [ "$failures" -gt 0 ]; then
        echo ""
        echo "$failures script(s) failed"
        exit 1
    fi

# Run all checks
all: lint format-check typecheck test
