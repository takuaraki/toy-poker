"""Tests for strategy evaluation (EV, exploitability)."""

from __future__ import annotations

import pytest

from toy_poker.games.kuhn import KuhnGame
from toy_poker.solvers.cfr import CFRSolver
from toy_poker.solvers.evaluate import expected_returns, exploitability


def test_kuhn_uniform_strategy_has_large_exploitability() -> None:
    game = KuhnGame()
    # 未学習の average_strategy は一様
    strategy = CFRSolver(game).average_strategy()
    assert expected_returns(game, strategy) == pytest.approx([1 / 8, -1 / 8])
    assert exploitability(game, strategy) > 0.1


def test_kuhn_cfr_strategy_has_small_exploitability() -> None:
    game = KuhnGame()
    solver = CFRSolver(game)
    for _ in range(5_000):
        solver.iterate()

    strategy = solver.average_strategy()
    assert exploitability(game, strategy) < 0.01
