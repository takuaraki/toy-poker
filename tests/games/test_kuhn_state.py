"""State field and immutability tests."""

from __future__ import annotations

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
from toy_poker.games.kuhn import KuhnState


class TestStateFields:
    def test_initial_pot_and_contributions(self) -> None:
        state = new_game().new_initial_state()
        assert state.pot == 2
        assert state.contributions == (1, 1)
        assert state.first_bettor == -1
        assert state.winner == -1

    def test_bet_updates_pot_and_contributions(self) -> None:
        state = deal_cards(new_game().new_initial_state(), K, Q)
        before = state
        after = state.apply_action(BET)
        assert after.pot == 3
        assert after.contributions == (2, 1)
        assert after.first_bettor == 0
        assert before.pot == 2

    def test_check_bet_call_final_pot(self) -> None:
        state = play_actions(
            deal_cards(new_game().new_initial_state(), K, J),
            [CHECK, BET, CALL],
        )
        assert state.pot == 4
        assert state.contributions == (2, 2)

    def test_player_cards_after_deal(self) -> None:
        state = deal_cards(new_game().new_initial_state(), 2, 0)  # P0=K, P1=J
        assert state.player_card(0) == 2
        assert state.player_card(1) == 0

    def test_current_player_alternates(self) -> None:
        state = deal_cards(new_game().new_initial_state(), Q, J)
        assert state.current_player() == 0
        state = state.apply_action(CHECK)
        assert state.current_player() == 1


class TestImmutability:
    def test_apply_action_does_not_mutate_original(self) -> None:
        state = deal_cards(new_game().new_initial_state(), K, Q)
        original_history_len = len(state.history)
        next_state = state.apply_action(BET)
        assert len(state.history) == original_history_len
        assert len(next_state.history) == original_history_len + 1
        assert isinstance(state, KuhnState)
        assert isinstance(next_state, KuhnState)
