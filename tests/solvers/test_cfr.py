"""Tests for the CFR solver."""

from __future__ import annotations

import pytest

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action
from toy_poker.games.kuhn import KuhnGame
from toy_poker.games.leduc import LeducGame
from toy_poker.solvers.cfr import CFRSolver, Strategy, regret_matching_strategy
from toy_poker.trees.traverse import collect_infosets


def _assert_strategy_is_distribution(
    strategy: Strategy, infosets: dict[str, list[Action]]
) -> None:
    assert set(strategy) == set(infosets)
    for key, actions in infosets.items():
        probs = strategy[key]
        assert set(probs) == set(actions)
        assert all(prob >= 0.0 for prob in probs.values())
        assert sum(probs.values()) == pytest.approx(1.0)


def expected_returns(game: Game, strategy: Strategy) -> list[float]:
    """Expected payoffs when both players follow ``strategy``."""

    def walk(state: State) -> list[float]:
        if state.is_terminal():
            return list(state.returns())

        if state.is_chance_node():
            values = [0.0, 0.0]
            for action, prob in state.chance_outcomes():
                child_values = walk(state.apply_action(action))
                values[0] += child_values[0] * prob
                values[1] += child_values[1] * prob
            return values

        player = state.current_player()
        key = state.information_state_string(player)
        probs = strategy[key]
        values = [0.0, 0.0]
        for action in state.legal_actions():
            child_values = walk(state.apply_action(action))
            values[0] += child_values[0] * probs[action]
            values[1] += child_values[1] * probs[action]
        return values

    return walk(game.new_initial_state())


@pytest.mark.parametrize(
    ("regrets", "expected"),
    [
        ({0: 2.0, 1: 1.0}, {0: 2 / 3, 1: 1 / 3}),
        ({0: -1.0, 1: 3.0}, {0: 0.0, 1: 1.0}),
        ({0: -1.0, 1: -2.0}, {0: 0.5, 1: 0.5}),
        ({0: 0.0, 1: 0.0}, {0: 0.5, 1: 0.5}),
        ({0: 0.0, 1: 4.0, 2: -3.0}, {0: 0.0, 1: 1.0, 2: 0.0}),
        ({0: 0.0, 1: 0.0, 2: 0.0}, {0: 1 / 3, 1: 1 / 3, 2: 1 / 3}),
    ],
    ids=[
        "proportional",
        "negative_gets_zero",
        "all_negative_uniform",
        "all_zero_uniform",
        "three_actions_mixed",
        "three_actions_uniform",
    ],
)
def test_regret_matching(
    regrets: dict[Action, float], expected: dict[Action, float]
) -> None:
    assert regret_matching_strategy(regrets) == pytest.approx(expected)


@pytest.mark.parametrize(
    "regrets",
    [
        {0: 2.0, 1: 1.0},
        {0: -5.0, 1: 0.5, 2: 7.25},
        {0: -1.0, 1: -1.0, 2: -1.0},
    ],
)
def test_regret_matching_is_probability_distribution(
    regrets: dict[Action, float],
) -> None:
    strategy = regret_matching_strategy(regrets)
    assert set(strategy) == set(regrets)
    assert all(prob >= 0.0 for prob in strategy.values())
    assert sum(strategy.values()) == pytest.approx(1.0)


def test_regret_matching_does_not_mutate_input() -> None:
    regrets = {0: -1.0, 1: 3.0}
    regret_matching_strategy(regrets)
    assert regrets == {0: -1.0, 1: 3.0}


# イテレーション1回目は後悔値がすべて 0 なので一様に打つ
# 一様に打ったときの期待値と一致するか確認する
# - Kuhn: 手計算の値
# - Leduc: 木全体を分数で厳密に数え上げた値。同じ Leduc 実装を使うため、
#   _cfr の期待値計算は検証できるが、ゲームのルール自体の正しさは保証しない
@pytest.mark.parametrize(
    ("game", "expected"),
    [
        (KuhnGame(), [1 / 8, -1 / 8]),
        (LeducGame(), [-5 / 64, 5 / 64]),
    ],
    ids=["kuhn", "leduc"],
)
def test_first_iteration_value(game: Game, expected: list[float]) -> None:
    values = CFRSolver(game).iterate()
    assert values == pytest.approx(expected)


@pytest.mark.parametrize("game", [KuhnGame(), LeducGame()], ids=["kuhn", "leduc"])
def test_average_strategy_untrained_is_uniform(game: Game) -> None:
    infosets = collect_infosets(game)
    strategy = CFRSolver(game).average_strategy()
    _assert_strategy_is_distribution(strategy, infosets)
    for key, actions in infosets.items():
        expected = {action: 1.0 / len(actions) for action in actions}
        assert strategy[key] == pytest.approx(expected)


@pytest.mark.parametrize("game", [KuhnGame(), LeducGame()], ids=["kuhn", "leduc"])
def test_average_strategy_after_iterate_is_distribution(game: Game) -> None:
    solver = CFRSolver(game)
    solver.iterate()
    strategy = solver.average_strategy()
    _assert_strategy_is_distribution(strategy, solver.infosets)


def test_average_strategy_does_not_mutate_strategy_sum() -> None:
    solver = CFRSolver(KuhnGame())
    solver.iterate()
    before = {
        key: dict(action_sums) for key, action_sums in solver.strategy_sum.items()
    }
    solver.average_strategy()
    assert solver.strategy_sum == before


def test_kuhn_average_strategy_approaches_nash() -> None:
    # 要件: Kuhn の均衡 EV は P0 = -1/18（許容 ±0.01）
    game = KuhnGame()
    solver = CFRSolver(game)
    for _ in range(5_000):
        solver.iterate()

    values = expected_returns(game, solver.average_strategy())
    assert values[0] == pytest.approx(-1 / 18, abs=0.01)
    assert values[1] == pytest.approx(1 / 18, abs=0.01)
