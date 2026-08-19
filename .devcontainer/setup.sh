#!/usr/bin/env bash
# Codespace bootstrap. Idempotent: safe to re-run.
set -euo pipefail

echo "==> Installing uv"
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

echo "==> Python dependencies"
uv sync --extra dev

echo "==> Interface dependencies"
(cd web && npm install --no-audit --no-fund)

echo "==> Seeding the registry"
uv run python scripts/seed.py || true

echo
echo "==> Verifying the gates, so a fresh Codespace proves itself rather than assuming"
uv run python -m pytest -q
python3 scripts/audit/register_lint.py
python3 scripts/audit/verify_grounding.py

cat <<'BANNER'

  MIZAN is ready.

    make dev      API on 8000, interface on 5173
    make test     the full suite
    make prove    the measured reduction proof
    make demo     the Fatima journey, offline

  Every claim in this repository has a command behind it. See CONTRIBUTING.md.

BANNER
