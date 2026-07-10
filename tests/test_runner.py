"""Tests for hand runner and formatting."""

from __future__ import annotations

from tests.games.helpers import BET, CALL, CHECK, deal_cards, new_game, play_actions
from tests.games.leduc_helpers import (
    CALL as LEDUC_CALL,
)
from tests.games.leduc_helpers import (
    FOLD as LEDUC_FOLD,
)
from tests.games.leduc_helpers import (
    JS,
    KH,
    KS,
    RAISE,
    deal_private,
    play_round1,
    play_round2,
)
from tests.games.leduc_helpers import (
    new_game as new_leduc_game,
)
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


def test_leduc_run_hand_completes() -> None:
    game = new_leduc_game()
    rng = make_rng(0)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    result = run_hand(game, agents, rng)
    assert result.final_state.is_terminal()
    assert len(result.returns) == 2
    assert abs(result.returns[0] + result.returns[1]) < 1e-9


def test_leduc_run_match_statistics() -> None:
    game = new_leduc_game()
    rng = make_rng(99)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    match = run_match(game, agents, num_hands=50, rng=rng)
    assert match.num_hands == 50
    assert abs(match.mean_returns[0] + match.mean_returns[1]) < 1e-9


def test_format_leduc_raise_fold() -> None:
    state = deal_private(new_leduc_game().new_initial_state(), KS, JS)
    state = play_round1(state, [RAISE, LEDUC_FOLD])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "=== Leduc Hold'em (2p) ===" in text
    assert "Deal: P0=Ks, P1=Js" in text
    assert "R1 P0: RAISE" in text
    assert "P1 folds" in text
    assert "Pot: 4 | Returns: P0=+1.0, P1=-1.0" in text


def test_format_leduc_showdown() -> None:
    state = deal_private(new_leduc_game().new_initial_state(), KS, JS)
    state = play_round1(state, [LEDUC_CALL, LEDUC_CALL])
    state = play_round2(state, KH, [LEDUC_CALL, LEDUC_CALL])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "Public: Kh" in text
    assert "Showdown: P0=Ks beats P1=Js (board=Kh)" in text
    assert "Pot: 2 | Returns: P0=+1.0, P1=-1.0" in text

def test_format_leduc_split_pot() -> None:
    state = deal_private(new_leduc_game().new_initial_state(), KS, KH)
    state = play_round1(state, [LEDUC_CALL, LEDUC_CALL])
    state = play_round2(state, JS, [LEDUC_CALL, LEDUC_CALL])
    text = format_hand(HandResult(returns=state.returns(), final_state=state))
    assert "Showdown: split pot (P0=Ks, P1=Kh; board=Js)" in text
    assert "Pot: 2 | Returns: P0=+0.0, P1=+0.0" in text
