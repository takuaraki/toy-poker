"""Shared type aliases."""

from __future__ import annotations

PlayerId = int
Payoff = float
Action = int
ChanceOutcome = tuple[Action, float]
Strategy = dict[str, dict[Action, float]]  # infoset キー → 行動 → 確率
