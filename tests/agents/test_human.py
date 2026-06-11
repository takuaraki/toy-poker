"""Tests for HumanAgent."""

from __future__ import annotations

import pytest

from toy_poker.agents.human import AnnouncingAgent, HumanAgent
from toy_poker.agents.random import RandomAgent
from toy_poker.core.rng import make_rng
from toy_poker.games.kuhn import KuhnAction, KuhnGame

CHECK = KuhnAction.PASS
BET = KuhnAction.BET
CALL = KuhnAction.BET
FOLD = KuhnAction.PASS


def deal_cards(state, p0_card: int, p1_card: int):
    state = state.apply_action(p0_card)
    return state.apply_action(p1_card)


@pytest.fixture
def checked_state():
    game = KuhnGame()
    return deal_cards(game.new_initial_state(), 2, 1)  # P0=K


def test_human_selects_check(checked_state) -> None:
    inputs = iter(["1"])
    outputs: list[str] = []
    agent = HumanAgent(
        player_id=0,
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    action = agent.select_action(checked_state, 0, [CHECK, BET])
    assert action == CHECK
    assert any("Your card: K" in line for line in outputs)
    assert any("CHECK" in line for line in outputs)


def test_human_selects_bet(checked_state) -> None:
    inputs = iter(["2"])
    agent = HumanAgent(
        player_id=0,
        input_fn=lambda _: next(inputs),
        output_fn=lambda _: None,
    )
    action = agent.select_action(checked_state, 0, [CHECK, BET])
    assert action == BET


def test_human_rejects_invalid_input_then_accepts(checked_state) -> None:
    inputs = iter(["x", "0", "2"])
    outputs: list[str] = []
    agent = HumanAgent(
        player_id=0,
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    action = agent.select_action(checked_state, 0, [CHECK, BET])
    assert action == BET
    assert any("Invalid input" in line for line in outputs)
    assert any("Invalid choice" in line for line in outputs)


def test_human_facing_bet_shows_fold_and_call(checked_state) -> None:
    state = checked_state.apply_action(CHECK).apply_action(BET)
    inputs = iter(["1"])
    outputs: list[str] = []
    agent = HumanAgent(
        player_id=0,
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    action = agent.select_action(state, 0, [FOLD, CALL])
    assert action == FOLD
    assert any("FOLD" in line for line in outputs)
    assert any("CALL" in line for line in outputs)


def test_human_wrong_player_raises(checked_state) -> None:
    agent = HumanAgent(player_id=0)
    with pytest.raises(ValueError, match="cannot act for P1"):
        agent.select_action(checked_state, 1, [CHECK, BET])


def test_announcing_agent_prints_action(checked_state) -> None:
    outputs: list[str] = []
    rng = make_rng(0)
    agent = AnnouncingAgent(
        RandomAgent(rng),
        player_id=0,
        output_fn=outputs.append,
    )
    agent.select_action(checked_state, 0, [CHECK, BET])
    assert len(outputs) == 1
    assert outputs[0].startswith("P0:")
