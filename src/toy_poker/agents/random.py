"""Random-action agent."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from toy_poker.core.protocols import State
from toy_poker.core.types import Action, PlayerId


@dataclass
class RandomAgent:
    """Selects uniformly at random from legal actions."""

    rng: np.random.Generator

    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action:
        del state, player
        index = self.rng.integers(len(legal_actions))
        return legal_actions[index]
