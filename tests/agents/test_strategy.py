"""Tests for StrategyAgent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from toy_poker.agents.strategy import StrategyAgent
from toy_poker.core.rng import make_rng
from toy_poker.core.types import Action, ChanceOutcome, Payoff, PlayerId, Strategy

INFOSET = "I0"
PASS = 0
BET = 1


@dataclass(frozen=True)
class _FakeState:
    """Minimal State stub; StrategyAgent only reads the infoset key."""

    infoset: str = INFOSET

    def is_terminal(self) -> bool:
        return False

    def is_chance_node(self) -> bool:
        return False

    def current_player(self) -> PlayerId:
        return 0

    def legal_actions(self) -> list[Action]:
        return [PASS, BET]

    def chance_outcomes(self) -> list[ChanceOutcome]:
        return []

    def apply_action(self, action: Action) -> _FakeState:
        del action
        return self

    def returns(self) -> list[Payoff]:
        return [0.0, 0.0]

    def action_history(self) -> list[str]:
        return []

    def information_state_string(self, player: PlayerId) -> str:
        del player
        return self.infoset


def _agent(
    strategy: Strategy,
    *,
    seed: int = 0,
    mode: Literal["sample", "argmax"] = "sample",
) -> StrategyAgent:
    return StrategyAgent(strategy=strategy, rng=make_rng(seed), mode=mode)


def test_argmax_selects_highest_probability_action() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.2, BET: 0.8}}
    agent = _agent(strategy, mode="argmax")
    assert agent.select_action(_FakeState(), 0, [PASS, BET]) == BET


def test_argmax_tie_breaks_toward_earlier_legal_action() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.5, BET: 0.5}}
    agent = _agent(strategy, mode="argmax")
    assert agent.select_action(_FakeState(), 0, [PASS, BET]) == PASS
    assert agent.select_action(_FakeState(), 0, [BET, PASS]) == BET


def test_sample_is_deterministic_with_fixed_seed() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.3, BET: 0.7}}
    state = _FakeState()
    legal = [PASS, BET]

    agent_a = _agent(strategy, seed=7)
    agent_b = _agent(strategy, seed=7)
    seq_a = [agent_a.select_action(state, 0, legal) for _ in range(20)]
    seq_b = [agent_b.select_action(state, 0, legal) for _ in range(20)]

    assert seq_a == seq_b
    assert set(seq_a).issubset({PASS, BET})


def test_sample_with_deterministic_distribution() -> None:
    strategy: Strategy = {INFOSET: {PASS: 1.0, BET: 0.0}}
    agent = _agent(strategy, seed=0, mode="sample")
    state = _FakeState()
    for _ in range(10):
        assert agent.select_action(state, 0, [PASS, BET]) == PASS


def test_zero_weights_fallback_argmax_picks_first_legal() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.0, BET: 0.0}}
    agent = _agent(strategy, mode="argmax")
    assert agent.select_action(_FakeState(), 0, [PASS, BET]) == PASS
    assert agent.select_action(_FakeState(), 0, [BET, PASS]) == BET


def test_zero_weights_fallback_sample_uses_both_actions() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.0, BET: 0.0}}
    agent = _agent(strategy, seed=0, mode="sample")
    state = _FakeState()
    legal = [PASS, BET]
    seen = {agent.select_action(state, 0, legal) for _ in range(50)}
    assert seen == {PASS, BET}


def test_renormalizes_over_legal_actions_only() -> None:
    # 非合法の行動に大きな確率があっても無視し、合法手だけで選ぶ
    strategy: Strategy = {INFOSET: {PASS: 0.1, BET: 0.1, 99: 0.8}}
    agent = _agent(strategy, mode="argmax")
    assert agent.select_action(_FakeState(), 0, [PASS, BET]) == PASS

    # BET だけ合法なら、テーブル上は同率でも BET を返す
    assert agent.select_action(_FakeState(), 0, [BET]) == BET


def test_missing_action_in_table_treated_as_zero() -> None:
    strategy: Strategy = {INFOSET: {PASS: 0.0}}  # BET キーなし
    agent = _agent(strategy, mode="argmax")
    # 合法手の重みがすべて 0 → 一様フォールバック → 先頭
    assert agent.select_action(_FakeState(), 0, [PASS, BET]) == PASS

    strategy_bet: Strategy = {INFOSET: {BET: 1.0}}
    agent_bet = _agent(strategy_bet, mode="argmax")
    assert agent_bet.select_action(_FakeState(), 0, [PASS, BET]) == BET
