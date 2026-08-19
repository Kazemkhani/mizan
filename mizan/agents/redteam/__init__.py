"""mizan.agents.redteam -- red-team probe engine, taxonomy, and rubric.

Public interface (Wave 1):
    SENTINEL_TAXONOMY     -- the bilingual jailbreak taxonomy dict
    RefusalIntegrityRubric -- the SENTINEL refusal-integrity rubric class

The probe engine reuses mizan.agents.harness.runner.run_suite().
Red-team suites are stored in suites/redteam/redteam.json (English attack
set, owned by SENTINEL) and suites/arabic/redteam.json (Arabic-native
attack set, owned by RASHID). The engine executes both as first-class
citizens from the same runner interface.
"""

from mizan.agents.redteam.rubric import RefusalIntegrityRubric
from mizan.agents.redteam.taxonomy import SENTINEL_TAXONOMY

__all__ = ["SENTINEL_TAXONOMY", "RefusalIntegrityRubric"]
