#!/usr/bin/env bash
set -euo pipefail

if [[ -f requirements.txt ]]; then
  python -m pip install --upgrade pip
  pip install -r requirements.txt
fi

if [[ -f package.json ]]; then
  npm install
fi

echo "Dev container pronto."
