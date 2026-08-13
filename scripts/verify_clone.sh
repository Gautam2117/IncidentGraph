#!/usr/bin/env bash
set -euo pipefail

echo "========================================="
echo "IncidentGraph Clean-Clone Verification"
echo "========================================="

# 1. Verify required tools
echo "[1/5] Checking environment requirements..."
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required"; exit 1; }

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Found Python version: ${PYTHON_VERSION}"

if command -v docker >/dev/null 2>&1; then
  echo "Found Docker CLI."
else
  echo "Warning: docker CLI not detected in PATH (make sure Docker Desktop is installed for docker-compose)."
fi

# 2. Check configuration blueprint
echo "[2/5] Checking configuration blueprint..."
if [ ! -f ".env.example" ]; then
  echo "Error: .env.example missing!"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

# 3. Check virtual environment
echo "[3/5] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
./.venv/bin/pip install --quiet --upgrade pip setuptools wheel
./.venv/bin/pip install --quiet -e ".[dev]"

# 4. Run lint and static type checks
echo "[4/5] Running static analysis & type checks..."
./.venv/bin/ruff check services/control-plane/
PYTHONPATH=services/control-plane:. ./.venv/bin/mypy services/control-plane/app services/demo/common

# 5. Execute unit tests
echo "[5/5] Executing unit & contract tests..."
PYTHONPATH=services/control-plane:. ./.venv/bin/pytest services/control-plane/tests -v

echo "========================================="
echo "Clean-clone bootstrap verification SUCCESS!"
echo "========================================="
