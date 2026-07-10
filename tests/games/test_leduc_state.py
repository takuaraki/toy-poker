"""Leduc state API tests."""

from __future__ import annotations

import pytest

from tests.games.leduc_helpers import CALL, JS, KS, deal_private, new_game, play_round1
from toy_poker.games.leduc import LeducAction


class TestReturns:
    def test_returns_undefined_before_terminal(self) -> None:
        state = deal_private(new_game().new_initial_state(), 0, 1)
        with pytest.raises(ValueError, match="only defined on terminal"):
            state.returns()

    def test_current_player_undefined_on_chance(self) -> None:
        state = new_game().new_initial_state()
        with pytest.raises(ValueError, match="chance nodes"):
            state.current_player()

    def test_current_player_undefined_on_terminal(self) -> None:
        state = deal_private(new_game().new_initial_state(), KS, JS)
        state = play_round1(state, [LeducAction.RAISE, LeducAction.FOLD])
        assert state.is_terminal()
        with pytest.raises(ValueError, match="terminal"):
            state.current_player()


class TestChanceOutcomes:
    def test_uniform_over_remaining_cards(self) -> None:
        state = new_game().new_initial_state()
        outcomes = state.chance_outcomes()
        assert len(outcomes) == 6
        assert all(prob == pytest.approx(1 / 6) for _, prob in outcomes)

    def test_five_cards_after_one_dealt(self) -> None:
        state = new_game().new_initial_state().apply_action(0)
        outcomes = state.chance_outcomes()
        assert len(outcomes) == 5
        assert 0 not in [card for card, _ in outcomes]

    def test_four_cards_for_public_deal(self) -> None:
        state = deal_private(new_game().new_initial_state(), KS, JS)
        state = play_round1(state, [CALL, CALL])
        assert state.is_chance_node()
        outcomes = state.chance_outcomes()
        remaining = [card for card, _ in outcomes]
        assert len(remaining) == 4
        assert KS not in remaining
        assert JS not in remaining
        assert all(prob == pytest.approx(1 / 4) for _, prob in outcomes)


class TestClonePath:
    def test_apply_action_does_not_mutate(self) -> None:
        initial = deal_private(new_game().new_initial_state(), 4, 0)
        next_state = initial.apply_action(CALL)
        assert initial.cur_player == 0
        assert next_state.cur_player == 1
        assert initial.round1_sequence == ()
        assert next_state.round1_sequence == (LeducAction.CALL,)
