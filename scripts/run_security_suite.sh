#!/bin/bash

# Targeted security regression runner for pre-release checks.
# This bypasses the global coverage gate so security suites can be
# exercised independently of broader coverage work in progress.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🛡️  Running security regression suite (coverage disabled)"

PYTHONPATH="${ROOT_DIR}/src:${ROOT_DIR}" \
pytest \
  --override-ini "addopts=--strict-markers --strict-config --verbose --tb=short --durations=10" \
  tests/security/ \
  "$@"

echo "✅ Security regression suite completed"
