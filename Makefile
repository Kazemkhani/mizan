# MIZAN Makefile
# Repository root: ~/work/mizan
#
# Targets:
#   dev    -- start API (port 8000) and web shell (port 5173) concurrently
#   api    -- start the FastAPI server only
#   web    -- start the Vite dev server only
#   test   -- run the Python test suite via pytest
#   seed   -- populate the database with demo data
#   reset  -- drop and reinitialise the database, then seed
#   lint   -- run the register discipline linter
#   clean  -- remove generated files (database, Python caches)
#
# Wave 3 additions (hooks left clean):
#   demo   -- run the choreographed demo flow
#   prove  -- run the reduction proof script

.PHONY: dev api web test seed reset lint clean

PYTHON := uv run python
PYTEST := uv run pytest

# ---------------------------------------------------------------------------
# dev: bring up API and web shell concurrently
# ---------------------------------------------------------------------------
dev:
	@echo "Starting MIZAN API (port 8000) and web shell (port 5173)..."
	@$(MAKE) -j2 api web

api:
	uv run uvicorn mizan.api.main:app --reload --host 0.0.0.0 --port 8000

web:
	cd web && npm run dev

# ---------------------------------------------------------------------------
# test: run the Python test suite
# ---------------------------------------------------------------------------
test:
	$(PYTEST) -v

# ---------------------------------------------------------------------------
# seed: populate the database with demo data
# ---------------------------------------------------------------------------
seed:
	$(PYTHON) scripts/seed.py

# ---------------------------------------------------------------------------
# reset: drop and reinitialise the database, then seed
# ---------------------------------------------------------------------------
reset:
	$(PYTHON) scripts/reset.py

# ---------------------------------------------------------------------------
# lint: run the register discipline linter
# ---------------------------------------------------------------------------
lint:
	$(PYTHON) scripts/audit/register_lint.py

# ---------------------------------------------------------------------------
# clean: remove generated artefacts
# ---------------------------------------------------------------------------
clean:
	rm -rf data/mizan.db
	find . -type d -name __pycache__ -not -path './.git/*' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# ---------------------------------------------------------------------------
# Wave 3 hooks (not yet wired; targets exist so later Makefile edits are minimal)
# ---------------------------------------------------------------------------
demo:
	@echo "Wave 4 target: not yet implemented."

prove:
	@echo "Wave 2 target: not yet implemented."
	@echo "Run: $(PYTHON) scripts/prove_reduction.py"
