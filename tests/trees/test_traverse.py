"""Tests for game tree traversal."""

from __future__ import annotations

import pytest

from toy_poker.core.protocols import Game
from toy_poker.games.kuhn import KuhnGame
from toy_poker.games.leduc import LeducGame
from toy_poker.trees.traverse import traverse_game_tree


def _count_nodes(game: Game) -> dict[str, int]:
    counts = {"chance": 0, "player": 0, "terminal": 0}
    for state in traverse_game_tree(game):
        if state.is_terminal():
            counts["terminal"] += 1
        elif state.is_chance_node():
            counts["chance"] += 1
        else:
            counts["player"] += 1
    return counts


@pytest.mark.parametrize(
    ("game", "expected"),
    [
        (KuhnGame(), {"chance": 4, "player": 24, "terminal": 30}),
        (LeducGame(), {"chance": 157, "player": 3780, "terminal": 5520}),
    ],
    ids=["kuhn", "leduc"],
)
def test_node_counts(game: Game, expected: dict[str, int]) -> None:
    assert _count_nodes(game) == expected


def test_first_state_is_root() -> None:
    first = next(iter(traverse_game_tree(KuhnGame())))
    assert first.is_chance_node()
    assert first.action_history() == []


def test_kuhn_terminals_are_zero_sum() -> None:
    for state in traverse_game_tree(KuhnGame()):
        if state.is_terminal():
            assert sum(state.returns()) == pytest.approx(0.0)


def test_kuhn_expected_value_of_terminals_under_uniform_chance() -> None:
    # 6 deals x 5 betting paths: each deal appears once per path
    terminals = [s for s in traverse_game_tree(KuhnGame()) if s.is_terminal()]
    deals = {tuple(s.action_history()[:2]) for s in terminals}
    assert len(deals) == 6
