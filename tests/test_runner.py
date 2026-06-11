"""Tests for hand runner and formatting."""

from __future__ import annotations

from toy_poker.agents.random import RandomAgent
from toy_poker.core.rng import make_rng
from toy_poker.games.kuhn import KuhnAction, KuhnGame
from toy_poker.runner.format import format_hand
from toy_poker.runner.hand import run_hand, run_match

CHECK = KuhnAction.PASS
BET = KuhnAction.BET
CALL = KuhnAction.BET
FOLD = KuhnAction.PASS


def deal_cards(state, p0_card: int, p1_card: int):
    state = state.apply_action(p0_card)
    return state.apply_action(p1_card)


def play_actions(state, actions: list[KuhnAction]):
    for action in actions:
        state = state.apply_action(action)
    return state


def test_run_hand_completes() -> None:
    game = KuhnGame()
    rng = make_rng(0)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    result = run_hand(game, agents, rng)
    assert result.final_state.is_terminal()
    assert len(result.returns) == 2
    assert result.returns[0] + result.returns[1] == 0.0


def test_run_hand_reproducible() -> None:
    game = KuhnGame()

    def play(seed: int) -> tuple[list[float], list[str]]:
        rng = make_rng(seed)
        agents = [RandomAgent(rng), RandomAgent(rng)]
        result = run_hand(game, agents, rng)
        return result.returns, result.final_state.action_history()

    assert play(123) == play(123)

    history_123, history_456 = play(123)[1], play(456)[1]
    assert history_123 != history_456


def test_run_match_statistics() -> None:
    game = KuhnGame()
    rng = make_rng(99)
    agents = [RandomAgent(rng), RandomAgent(rng)]
    match = run_match(game, agents, num_hands=100, rng=rng)
    assert match.num_hands == 100
    assert len(match.mean_returns) == 2
    assert len(match.std_returns) == 2
    assert match.mean_returns[0] + match.mean_returns[1] == 0.0


def test_format_hand_bet_call_showdown() -> None:
    game = KuhnGame()
    state = deal_cards(game.new_initial_state(), 2, 1)  # P0=K, P1=Q
    state = play_actions(state, [BET, CALL])
    result = run_hand_from_state(state)
    text = format_hand(result)
    assert "=== Kuhn Poker (2p) ===" in text
    assert "Deal: P0=K, P1=Q" in text
    assert "P0: BET" in text
    assert "P1: CALL" in text
    assert "Showdown: P0=K beats P1=Q" in text
    assert "Pot: 4 | Returns: P0=+2.0, P1=-2.0" in text


def test_format_hand_check_check_showdown() -> None:
    game = KuhnGame()
    state = deal_cards(game.new_initial_state(), 2, 1)
    state = play_actions(state, [CHECK, CHECK])
    result = run_hand_from_state(state)
    text = format_hand(result)
    assert "P0: CHECK" in text
    assert "P1: CHECK" in text
    assert "Showdown: P0=K beats P1=Q" in text
    assert "Pot: 2 | Returns: P0=+1.0, P1=-1.0" in text


def test_format_hand_bet_fold() -> None:
    game = KuhnGame()
    state = deal_cards(game.new_initial_state(), 2, 0)
    state = play_actions(state, [BET, FOLD])
    result = run_hand_from_state(state)
    text = format_hand(result)
    assert "P0: BET" in text
    assert "P1: FOLD" in text
    assert "P1 folds" in text
    assert "Pot: 3 | Returns: P0=+1.0, P1=-1.0" in text


def run_hand_from_state(state):
    from toy_poker.runner.hand import HandResult

    return HandResult(returns=state.returns(), final_state=state)
