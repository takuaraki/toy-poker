"""Strategy-based agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from toy_poker.core.protocols import State
from toy_poker.core.types import Action, PlayerId
from toy_poker.solvers.cfr import Strategy


@dataclass
class StrategyAgent:
    """Selects actions based on a strategy."""

    strategy: Strategy
    rng: np.random.Generator
    mode: Literal["sample", "argmax"] = "sample"

    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action:
        key = state.information_state_string(player)
        probs = self.strategy[key]
        legal_probs = {action: probs.get(action, 0.0) for action in legal_actions}

        sum_legal_probs = sum(legal_probs.values())
        if sum_legal_probs > 0:
            normalized_probs = {
                action: legal_probs[action] / sum_legal_probs
                for action in legal_actions
            }
        else:
            # 合法手の重みの合計が0の場合は、一様分布にフォールバックする
            normalized_probs = {
                action: 1 / len(legal_actions) for action in legal_actions
            }

        if self.mode == "sample":
            weights = [normalized_probs[a] for a in legal_actions]
            return Action(self.rng.choice(legal_actions, p=weights))
        elif self.mode == "argmax":
            return Action(max(legal_actions, key=lambda a: normalized_probs[a]))
        else:
            raise ValueError(f"Invalid mode: {self.mode}")
