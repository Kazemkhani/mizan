"""UCB1 bandit allocator for adaptive compliance evaluation.

Public surface: BanditEngine. Everything else is internal.
"""

from mizan.engine.bandit.allocator import BanditEngine, ControlState, ArmState

__all__ = ["BanditEngine", "ControlState", "ArmState"]
