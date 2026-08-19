"""mizan.agents.harness -- suite runners and model endpoint adapters.

Public interface (Wave 1):
    run_suite(suite_id, model_endpoint, locale, evaluation_id) -> list[EvidenceRow]

Adapters:
    MockEndpoint(seed, profile)          -- deterministic offline adapter
    OpenAICompatibleEndpoint(url, ...)   -- live OpenAI-compatible adapter
"""

from mizan.agents.harness.adapters import MockEndpoint, OpenAICompatibleEndpoint
from mizan.agents.harness.runner import run_suite

__all__ = ["run_suite", "MockEndpoint", "OpenAICompatibleEndpoint"]
