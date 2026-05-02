#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="${SCRIPT_DIR}/frontend"
NPM_BIN="${NPM_BIN:-$(command -v npm)}"

if [ -z "${NPM_BIN}" ]; then
  echo "npm is required but was not found on PATH"
  exit 1
fi

cd "${FRONTEND_DIR}"
"${NPM_BIN}" install 2>&1
echo "EXIT_CODE: $?"
