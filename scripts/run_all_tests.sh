#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "IncidentGraph Master Test Suite & Audit Runner"
echo "=========================================================="

echo "[1/6] Running Ruff Linter & Syntax Check..."
./.venv/bin/ruff check services/control-plane/ services/demo/ scripts/

echo "[2/6] Running Mypy Static Type Analysis..."
PYTHONPATH=.:services/control-plane ./.venv/bin/mypy \
  services/control-plane/app services/control-plane/tests services/demo/common

echo "[3/6] Running Pytest Suite..."
PYTHONPATH=.:services/control-plane ./.venv/bin/pytest services/control-plane/tests -q

echo "[4/6] Running Console TypeScript Check..."
npm run typecheck --prefix apps/console

echo "[5/6] Running Console ESLint..."
npm run lint --prefix apps/console

echo "[6/6] Building Production Console Bundle..."
npm run build:console

echo "=========================================================="
echo "SUCCESS: ALL TESTS & AUDITS PASSED CLEANLY (100% PASS RATE)"
echo "=========================================================="
