"""Tests for hand runner and formatting."""

from __future__ import annotations

from tests.games.helpers import BET, CALL, CHECK, deal_cards, new_game, play_actions
from toy_poker.agents.random import RandomAgent
from toy_poker.core.rng import make_rng
from toy_poker.runner.format import format_hand
from toy_poker.runner.hand import HandResult, run_hand, run_match


def test_run_hand_completes() -> None:
    game = new_game()
    rng = make_rng(0)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    result = run_hand(game, agents, rng)
    assert result.final_state.is_terminal()
    assert len(result.returns) == 2
    assert result.returns[0] + result.returns[1] == 0.0


def test_run_match_statistics() -> None:
    game = new_game()
    rng = make_rng(99)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    match = run_match(game, agents, num_hands=100, rng=rng)
    assert match.num_hands == 100
    assert len(match.mean_returns) == 2
    assert match.mean_returns[0] + match.mean_returns[1] == 0.0


def test_format_hand_bet_call_showdown() -> None:
    state = play_actions(deal_cards(new_game().new_initial_state(), 2, 1), [BET, CALL])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "Showdown: P0=K beats P1=Q" in text
    assert "Pot: 4 | Returns: P0=+2.0, P1=-2.0" in text


def test_format_hand_check_check_showdown() -> None:
    initial = deal_cards(new_game().new_initial_state(), 2, 1)
    state = play_actions(initial, [CHECK, CHECK])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "P0: CHECK" in text
    assert "Pot: 2 | Returns: P0=+1.0, P1=-1.0" in text


def test_format_hand_bet_fold() -> None:
    state = play_actions(deal_cards(new_game().new_initial_state(), 2, 0), [BET, CHECK])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "P1 folds" in text
    assert "Pot: 3 | Returns: P0=+1.0, P1=-1.0" in text
