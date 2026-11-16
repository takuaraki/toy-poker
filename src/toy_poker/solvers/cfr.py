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
        self.infosets = collect_infosets(game)
        self.regret_sum = {
            k: {a: 0.0 for a in acts} for k, acts in self.infosets.items()
        }
        self.strategy_sum = {
            k: {a: 0.0 for a in acts} for k, acts in self.infosets.items()
        }
        self.reset_deltas()

    def reset_deltas(self) -> None:
        self.regret_delta = {
            k: {a: 0.0 for a in acts} for k, acts in self.infosets.items()
        }
        self.strategy_delta = {
            k: {a: 0.0 for a in acts} for k, acts in self.infosets.items()
        }

    def iterate(self) -> list[Payoff]:
        self.reset_deltas()
        values = self._cfr(self.game.new_initial_state(), 1.0, 1.0, 1.0)
        # 後悔値と戦略を更新
        for k, acts in self.infosets.items():
            for a in acts:
                self.regret_sum[k][a] += self.regret_delta[k][a]
                self.strategy_sum[k][a] += self.strategy_delta[k][a]
        return values

    def average_strategy(self) -> Strategy:
        raise NotImplementedError

    def _cfr(
        self, state: State, reach_p0: float, reach_p1: float, reach_chance: float
    ) -> list[Payoff]:
        # 終端ノードの場合
        if state.is_terminal():
            return state.returns()  # 利得を返す

        # チャンスノードの場合
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

        # 決定ノードの場合
        player = state.current_player()
        actions = state.legal_actions()
        infoset_key = state.information_state_string(player)
        strategy = regret_matching_strategy(self.regret_sum[infoset_key])

        # 期待利得を計算
        action_values: dict[Action, list[Payoff]] = {}  # 行動ごとの期待利得
        values = [0.0, 0.0]  # このノードでのプレイヤー0とプレイヤー1の期待利得
        for action in actions:
            prob = strategy[action]
            if player == 0:
                child_values = self._cfr(
                    state.apply_action(action),
                    reach_p0 * prob,
                    reach_p1,
                    reach_chance,
                )
            else:
                child_values = self._cfr(
                    state.apply_action(action),
                    reach_p0,
                    reach_p1 * prob,
                    reach_chance,
                )
            action_values[action] = child_values
            values[0] += child_values[0] * prob
            values[1] += child_values[1] * prob

        # 後悔値と戦略のdeltaを更新（イテレーション終了後にdeltaをsumに加算）
        regret_weight = (reach_p1 if player == 0 else reach_p0) * reach_chance
        strategy_weight = reach_p0 if player == 0 else reach_p1
        for action in actions:
            regret = action_values[action][player] - values[player]
            self.regret_delta[infoset_key][action] += regret * regret_weight
            self.strategy_delta[infoset_key][action] += (
                strategy[action] * strategy_weight
            )

        return values


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
