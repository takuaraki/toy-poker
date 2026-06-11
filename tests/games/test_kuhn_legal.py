"""Legal action tests at each node type."""

from __future__ import annotations

import pytest

from tests.games.helpers import BET, CHECK, J, K, Q, deal_cards, new_game
from toy_poker.games.kuhn import KuhnAction


class TestChanceLegalActions:
    def test_initial_deal_three_cards(self) -> None:
        state = new_game().new_initial_state()
        assert state.legal_actions() == [J, Q, K]

    def test_second_deal_two_remaining_cards(self) -> None:
        state = new_game().new_initial_state().apply_action(K)
        assert state.legal_actions() == [J, Q]

    def test_chance_outcomes_second_deal(self) -> None:
        state = new_game().new_initial_state().apply_action(Q)
        outcomes = state.chance_outcomes()
        assert len(outcomes) == 2
        assert sum(prob for _, prob in outcomes) == pytest.approx(1.0)
        assert all(prob == pytest.approx(0.5) for _, prob in outcomes)


class TestPlayerLegalActions:
    def test_root_betting_both_actions(self) -> None:
        state = deal_cards(new_game().new_initial_state(), Q, J)
        assert state.legal_actions() == [KuhnAction.PASS, KuhnAction.BET]

    def test_after_check_still_both_actions(self) -> None:
        state = deal_cards(new_game().new_initial_state(), K, Q).apply_action(CHECK)
        assert state.current_player() == 1
        assert state.legal_actions() == [KuhnAction.PASS, KuhnAction.BET]

    def test_facing_bet_fold_and_call(self) -> None:
        state = (
            deal_cards(new_game().new_initial_state(), J, K)
            .apply_action(CHECK)
            .apply_action(BET)
        )
        assert state.current_player() == 0
        assert state.legal_actions() == [KuhnAction.PASS, KuhnAction.BET]


class TestTerminalLegalActions:
    def test_terminal_has_no_legal_actions(self) -> None:
        state = deal_cards(new_game().new_initial_state(), K, Q)
        state = state.apply_action(CHECK).apply_action(CHECK)
        assert state.is_terminal()
        assert state.legal_actions() == []


class TestInvalidNodeAccess:
    def test_returns_on_non_terminal_raises(self) -> None:
        state = new_game().new_initial_state()
        with pytest.raises(ValueError, match="returns"):
            state.returns()

    def test_chance_outcomes_on_player_node_raises(self) -> None:
        state = deal_cards(new_game().new_initial_state(), J, Q)
        with pytest.raises(ValueError, match="chance node"):
            state.chance_outcomes()

    def test_current_player_on_chance_node_raises(self) -> None:
        state = new_game().new_initial_state()
        with pytest.raises(ValueError, match="chance nodes"):
            state.current_player()
