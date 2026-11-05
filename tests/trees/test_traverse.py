"""Tests for game tree traversal."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from toy_poker.core.protocols import Game
from toy_poker.core.types import Action, ChanceOutcome, Payoff, PlayerId
from toy_poker.games.kuhn import KuhnAction, KuhnGame
from toy_poker.games.leduc import LeducAction, LeducGame
from toy_poker.trees.traverse import collect_infosets, traverse_game_tree

KUHN_INFOSETS = {
    f"{card}{history}" for card in "012" for history in ("", "p", "b", "pb")
}


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


def test_kuhn_infoset_keys() -> None:
    assert set(collect_infosets(KuhnGame())) == KUHN_INFOSETS


def test_kuhn_infosets_have_pass_and_bet() -> None:
    for actions in collect_infosets(KuhnGame()).values():
        assert actions == [KuhnAction.PASS, KuhnAction.BET]


def test_leduc_infoset_count_matches_openspiel() -> None:
    # OpenSpiel leduc_poker.h: kNumInfoStates = 936
    assert len(collect_infosets(LeducGame())) == 936


def test_leduc_infoset_legal_actions() -> None:
    infosets = collect_infosets(LeducGame())
    # P0 opens round 1 holding Ks: check or raise, no fold
    assert infosets["4|x||"] == [LeducAction.CALL, LeducAction.RAISE]
    # Facing two raises: fold or call only
    assert infosets["4|x|rr|"] == [LeducAction.FOLD, LeducAction.CALL]


@dataclass(frozen=True)
class _InconsistentState:
    """Two nodes share infoset "x" but expose different legal actions."""

    depth: int
    branch: int = 0

    def is_terminal(self) -> bool:
        return self.depth == 2

    def is_chance_node(self) -> bool:
        return False

    def current_player(self) -> PlayerId:
        return 0 if self.depth == 0 else 1

    def legal_actions(self) -> list[Action]:
        if self.is_terminal():
            return []
        if self.depth == 0:
            return [0, 1]
        return [0] if self.branch == 0 else [0, 1]

    def chance_outcomes(self) -> list[ChanceOutcome]:
        raise ValueError("not a chance node")

    def apply_action(self, action: Action) -> _InconsistentState:
        if self.depth == 0:
            return _InconsistentState(depth=1, branch=action)
        return _InconsistentState(depth=2)

    def returns(self) -> list[Payoff]:
        return [0.0, 0.0]

    def action_history(self) -> list[str]:
        return []

    def information_state_string(self, player: PlayerId) -> str:
        return "root" if self.depth == 0 else "x"


class _InconsistentGame:
    def new_initial_state(self) -> _InconsistentState:
        return _InconsistentState(depth=0)

    def num_players(self) -> int:
        return 2

    def max_utility(self) -> float:
        return 0.0


def test_inconsistent_legal_actions_raise() -> None:
    with pytest.raises(ValueError, match="inconsistent legal actions"):
        collect_infosets(_InconsistentGame())
