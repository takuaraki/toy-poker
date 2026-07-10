"""Tests for HumanAgent."""

from __future__ import annotations

import pytest

from tests.games.helpers import BET, CALL, CHECK, FOLD, deal_cards, new_game
from tests.games.leduc_helpers import CALL as LEDUC_CALL
from tests.games.leduc_helpers import JS, KS, RAISE, deal_private
from tests.games.leduc_helpers import new_game as new_leduc_game
from toy_poker.agents.human import AnnouncingAgent, HumanAgent
from toy_poker.agents.random import RandomAgent
from toy_poker.core.rng import make_rng
from toy_poker.games.kuhn import KuhnState
from toy_poker.games.leduc import LeducState


@pytest.fixture
def checked_state() -> KuhnState:
    return deal_cards(new_game().new_initial_state(), 2, 1)  # P0=K


@pytest.fixture
def leduc_dealt() -> LeducState:
    return deal_private(new_leduc_game().new_initial_state(), KS, JS)


def test_human_selects_check(checked_state: KuhnState) -> None:
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


def test_human_rejects_invalid_input_then_accepts(checked_state: KuhnState) -> None:
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


def test_human_facing_bet_shows_fold_and_call(checked_state: KuhnState) -> None:
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


def test_human_wrong_player_raises(checked_state: KuhnState) -> None:
    agent = HumanAgent(player_id=0)
    with pytest.raises(ValueError, match="cannot act for P1"):
        agent.select_action(checked_state, 1, [CHECK, BET])


def test_announcing_agent_prints_action(checked_state: KuhnState) -> None:
    outputs: list[str] = []
    agent = AnnouncingAgent(
        RandomAgent(make_rng(0)),
        player_id=0,
        output_fn=outputs.append,
    )
    agent.select_action(checked_state, 0, [CHECK, BET])
    assert outputs[0].startswith("P0:")


def test_leduc_human_shows_card_and_public(leduc_dealt: LeducState) -> None:
    inputs = iter(["1"])
    outputs: list[str] = []
    agent = HumanAgent(
        player_id=0,
        input_fn=lambda _: next(inputs),
        output_fn=outputs.append,
    )
    action = agent.select_action(
        leduc_dealt, 0, list(leduc_dealt.legal_actions())
    )
    assert action == LEDUC_CALL
    assert any("Your card: Ks" in line for line in outputs)
    assert any("Public: (none)" in line for line in outputs)
    assert any("CHECK" in line for line in outputs)
    assert any("RAISE" in line for line in outputs)


def test_leduc_announcing_agent_prints_action(leduc_dealt: LeducState) -> None:
    outputs: list[str] = []
    agent = AnnouncingAgent(
        RandomAgent(make_rng(0)),
        player_id=0,
        output_fn=outputs.append,
    )
    agent.select_action(leduc_dealt, 0, [LEDUC_CALL, RAISE])
    assert outputs[0].startswith("P0:")
