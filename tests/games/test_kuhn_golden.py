"""Golden tests: all card deals x all terminal betting paths."""

from __future__ import annotations

import pytest

from tests.games.helpers import (
    TERMINAL_PATHS,
    all_card_deals,
    deal_cards,
    new_game,
    play_actions,
    reference_outcome,
)
from toy_poker.games.kuhn import KuhnAction


class TestGoldenTerminalStates:
    @pytest.mark.parametrize("p0_card,p1_card", list(all_card_deals()))
    @pytest.mark.parametrize(
        "actions",
        TERMINAL_PATHS,
        ids=lambda path: "-".join(str(action) for action in path),
    )
    def test_terminal_state_matches_reference(
        self,
        p0_card: int,
        p1_card: int,
        actions: tuple[KuhnAction, ...],
    ) -> None:
        game = new_game()
        initial = deal_cards(game.new_initial_state(), p0_card, p1_card)
        state = play_actions(initial, actions)

        exp_winner, exp_returns, exp_pot = reference_outcome(p0_card, p1_card, actions)

        assert state.is_terminal()
        assert state.winner == exp_winner
        assert state.pot == exp_pot
        assert state.returns() == exp_returns
        assert state.returns()[0] + state.returns()[1] == pytest.approx(0.0)
