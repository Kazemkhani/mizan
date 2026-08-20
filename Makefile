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

.PHONY: dev api web test seed reset lint clean demo prove

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

# The slow set, deselected from `make test` by the marker in pyproject.toml.
# Regenerates the full corpus to prove generation is deterministic.
test-slow:
	$(PYTEST) -v -m slow

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
# demo: run the Fatima Arabic Citizen Chatbot journey end to end.
#
# Performs the full pitch flow offline:
#   1. Submit Fatima's model against the Arabic Citizen Chatbot use case.
#   2. BanditEngine adjudicates via the deterministic mock endpoint.
#   3. A verdict is reached (certified or rejected).
#   4. A MIZAN compliance certificate is issued.
#   5. Elapsed seconds are printed; the run must complete within 90 seconds.
#
# Exits non-zero and names the missing piece if any step fails.
# ---------------------------------------------------------------------------
demo:
	$(PYTHON) scripts/run_demo.py

# ---------------------------------------------------------------------------
# prove: run the adaptive probe-budget reduction proof.
#
# Measures the reduction in probe budget achieved by BanditEngine versus an
# exhaustive baseline on the same models, suites, corpus, and decision rules.
# Writes the reduction report to docs/evidence/reduction_report.md.
# ---------------------------------------------------------------------------
prove:
	$(PYTHON) scripts/prove_reduction.py
