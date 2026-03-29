#!/usr/bin/env bash
# Regenerate all diagram outputs inside a Docker container that matches CI
# (ubuntu-latest + same graphviz). This ensures committed outputs are
# byte-identical to what CI produces.
#
# Usage: ./scripts/regenerate-outputs.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

docker run --rm \
  --platform linux/amd64 \
  -v "$REPO_ROOT":/workspace \
  -w /workspace/scripts \
  ubuntu:24.04 \
  bash -c '
    set -euo pipefail
    apt-get update -qq
    apt-get install -y -qq graphviz curl fonts-liberation fontconfig > /dev/null 2>&1
    fc-cache -f > /dev/null 2>&1

    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh > /dev/null 2>&1
    export PATH="$HOME/.local/bin:$PATH"

    SKIP="block-blockdiag.py sequence-seqdiag.py"
    for script in *.py; do
      if echo "$SKIP" | grep -qw "$script"; then
        echo "Skipping $script (unmaintained)"
        continue
      fi
      echo "Running $script ..."
      uv run "$script"
    done
    echo "Done. All outputs regenerated."
  '
