"""Tests for the CFR solver."""

from __future__ import annotations

import pytest

from toy_poker.core.types import Action
from toy_poker.solvers.cfr import regret_matching_strategy


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
