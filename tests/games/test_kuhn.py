"""Representative Kuhn Poker tests (see also test_kuhn_golden/legal/state)."""

from __future__ import annotations

import pytest

from tests.games.helpers import (
    BET,
    CALL,
    CHECK,
    J,
    K,
    Q,
    deal_cards,
    new_game,
    play_actions,
)


class TestChanceNode:
    def test_initial_is_chance(self) -> None:
        state = new_game().new_initial_state()
        assert state.is_chance_node()
        assert not state.is_terminal()
        assert state.legal_actions() == [J, Q, K]


class TestTransitions:
    """Representative terminal paths (full coverage in test_kuhn_golden)."""

    def test_check_check_showdown(self) -> None:
        initial = deal_cards(new_game().new_initial_state(), Q, J)
        state = play_actions(initial, [CHECK, CHECK])
        assert state.is_terminal()
        assert state.winner == 0

    def test_check_bet_call_showdown(self) -> None:
        initial = deal_cards(new_game().new_initial_state(), K, J)
        state = play_actions(initial, [CHECK, BET, CALL])
        assert state.is_terminal()
        assert state.winner == 0

    def test_illegal_actions_raise(self) -> None:
        state = new_game().new_initial_state().apply_action(J)
        with pytest.raises(ValueError, match="illegal chance action"):
            state.apply_action(J)
        state = deal_cards(new_game().new_initial_state(), J, Q)
        with pytest.raises(ValueError, match="illegal player action"):
            state.apply_action(99)


class TestInformationState:
    def test_infostate_matches_openspiel_style(self) -> None:
        state = deal_cards(new_game().new_initial_state(), K, Q).apply_action(BET)
        assert state.information_state_string(0) == "2b"
        assert state.information_state_string(1) == "1b"


class TestActionHistory:
    def test_history_strings(self) -> None:
        initial = deal_cards(new_game().new_initial_state(), K, Q)
        state = play_actions(initial, [BET, CALL])
        assert state.action_history() == [
            "Deal P0: K",
            "Deal P1: Q",
            "P0: Bet",
            "P1: Bet",
        ]
