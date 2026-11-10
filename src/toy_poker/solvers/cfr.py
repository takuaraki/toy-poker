"""Counterfactual regret minimization."""

from __future__ import annotations

from toy_poker.core.protocols import Game
from toy_poker.core.types import Action
from toy_poker.trees.traverse import collect_infosets

Strategy = dict[str, dict[Action, float]]  # infoset キー → 行動 → 確率


class CFRSolver:
    def __init__(self, game: Game) -> None:
        self.game = game

        # 累積regret、累積戦略を初期化
        infosets = collect_infosets(game)
        self.regret_sum = {k: {a: 0.0 for a in acts} for k, acts in infosets.items()}
        self.strategy_sum = {k: {a: 0.0 for a in acts} for k, acts in infosets.items()}

    def iterate(self) -> None:
        raise NotImplementedError

    def average_strategy(self) -> Strategy:
        raise NotImplementedError


def regret_matching_strategy(regrets: dict[Action, float]) -> dict[Action, float]:
    strategy: dict[Action, float] = {}
    total_positive_regret = sum(regret for regret in regrets.values() if regret > 0)

    if total_positive_regret > 0:
        for action, regret in regrets.items():
            if regret > 0:
                strategy[action] = regret / total_positive_regret
            else:
                strategy[action] = 0.0
    else:
        for action in regrets.keys():
            strategy[action] = 1.0 / len(regrets)

    return strategy
