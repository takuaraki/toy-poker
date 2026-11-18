"""Tests for strategy evaluation (EV, exploitability)."""

from __future__ import annotations

import pytest

from toy_poker.games.kuhn import KuhnGame
from toy_poker.games.leduc import LeducGame
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


def test_leduc_uniform_strategy_has_large_exploitability() -> None:
    game = LeducGame()
    strategy = CFRSolver(game).average_strategy()
    expl = exploitability(game, strategy)
    assert expl >= 0.0
    assert expl > 1.0


def test_leduc_cfr_reduces_exploitability() -> None:
    # 速いスモーク: 学習で下がることと非負であること（旧実装の負値バグの再発防止）
    game = LeducGame()
    uniform_expl = exploitability(game, CFRSolver(game).average_strategy())

    solver = CFRSolver(game)
    for _ in range(50):
        solver.iterate()
    cfr_expl = exploitability(game, solver.average_strategy())

    assert cfr_expl >= 0.0
    assert cfr_expl < uniform_expl
    assert cfr_expl < 0.5


@pytest.mark.slow
def test_leduc_cfr_exploitability_sufficiently_small() -> None:
    # 要件: Leduc で exploitability が十分小さい。CI では -m "not slow" で除外。
    game = LeducGame()
    solver = CFRSolver(game)
    for _ in range(1_000):
        solver.iterate()

    expl = exploitability(game, solver.average_strategy())
    assert expl >= 0.0
    assert expl < 0.05
