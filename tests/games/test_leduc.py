"""Representative Leduc Hold'em tests."""

from __future__ import annotations

import pytest

from tests.games.leduc_helpers import (
    CALL,
    FOLD,
    JH,
    JS,
    KH,
    KS,
    QH,
    QS,
    RAISE,
    assert_zero_sum,
    deal_private,
    new_game,
    play_round1,
    play_round2,
)
from toy_poker.games.leduc import LeducAction


class TestChanceNode:
    def test_initial_is_chance_with_six_cards(self) -> None:
        state = new_game().new_initial_state()
        assert state.is_chance_node()
        assert not state.is_terminal()
        assert state.legal_actions() == list(range(6))


class TestTransitions:
    def test_check_check_public_check_check_showdown(self) -> None:
        state = deal_private(new_game().new_initial_state(), KS, JS)
        state = play_round1(state, [CALL, CALL])
        assert state.is_chance_node()
        state = play_round2(state, QH, [CALL, CALL])
        assert state.is_terminal()
        assert state.winner == 0
        assert_zero_sum(state.returns())

    def test_round1_raise_call_ends_round(self) -> None:
        state = deal_private(new_game().new_initial_state(), JS, JH)
        state = play_round1(state, [RAISE, CALL])
        assert state.is_chance_node()
        assert state.round_number == 2
        assert state.pot == 6

    def test_fold_in_round1(self) -> None:
        state = deal_private(new_game().new_initial_state(), QS, QH)
        state = play_round1(state, [RAISE, FOLD])
        assert state.is_terminal()
        assert state.winner == 0
        assert state.returns() == [1.0, -1.0]
        assert_zero_sum(state.returns())

    def test_pair_beats_high_card(self) -> None:
        # P0: Ks, P1: Js, public: Kh -> P0 pair of Kings
        state = deal_private(new_game().new_initial_state(), KS, JS)
        state = play_round1(state, [CALL, CALL])
        state = play_round2(state, KH, [CALL, CALL])
        assert state.is_terminal()
        assert state.winner == 0
        assert_zero_sum(state.returns())

    def test_illegal_actions(self) -> None:
        state = new_game().new_initial_state().apply_action(JS)
        with pytest.raises(ValueError, match="illegal chance action"):
            state.apply_action(JS)
        state = deal_private(new_game().new_initial_state(), JS, JH)
        with pytest.raises(ValueError, match="illegal player action"):
            state.apply_action(99)


class TestLegalActions:
    def test_cannot_fold_when_checked_to(self) -> None:
        state = deal_private(new_game().new_initial_state(), JS, JH)
        assert LeducAction.FOLD not in state.legal_actions()
        assert state.legal_actions() == [LeducAction.CALL, LeducAction.RAISE]

    def test_can_fold_facing_raise(self) -> None:
        state = deal_private(new_game().new_initial_state(), JS, JH)
        state = state.apply_action(RAISE)
        assert state.legal_actions() == [
            LeducAction.FOLD,
            LeducAction.CALL,
            LeducAction.RAISE,
        ]

    def test_max_two_raises_per_round(self) -> None:
        state = deal_private(new_game().new_initial_state(), JS, JH)
        state = play_round1(state, [RAISE, RAISE, CALL])
        assert state.is_chance_node()
        assert state.round1_sequence == (RAISE, RAISE, CALL)


class TestInformationState:
    def test_infostate_encoding(self) -> None:
        state = deal_private(new_game().new_initial_state(), KS, QH)
        state = state.apply_action(RAISE)
        assert state.information_state_string(0) == "4|x|r|"
        assert state.information_state_string(1) == "3|x|r|"


class TestActionHistory:
    def test_history_strings(self) -> None:
        state = deal_private(new_game().new_initial_state(), KS, QH)
        state = play_round1(state, [RAISE, FOLD])
        assert state.action_history() == [
            "Deal P0: Ks",
            "Deal P1: Qh",
            "R1: Raise",
            "R1: Fold",
        ]
