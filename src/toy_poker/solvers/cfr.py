"""Counterfactual regret minimization."""

from __future__ import annotations

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action, Payoff
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

    def _cfr(
        self, state: State, reach_p0: float, reach_p1: float, reach_chance: float
    ) -> list[Payoff]:
        if state.is_terminal():
            return state.returns()  # 終端ノードの場合は利得を返す
        if state.is_chance_node():
            values = [0.0, 0.0]  # プレイヤー0とプレイヤー1の期待利得
            for action, prob in state.chance_outcomes():
                child_values = self._cfr(
                    state.apply_action(action),
                    reach_p0,
                    reach_p1,
                    reach_chance * prob,
                )
                values[0] += child_values[0] * prob
                values[1] += child_values[1] * prob
            return values

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
