"""Shared helpers for Leduc game tests."""

from __future__ import annotations

from toy_poker.games.leduc import LeducAction, LeducGame, LeducState

# Card ids: 0=Js, 1=Jh, 2=Qs, 3=Qh, 4=Ks, 5=Kh
JS, JH, QS, QH, KS, KH = 0, 1, 2, 3, 4, 5

FOLD = LeducAction.FOLD
CALL = LeducAction.CALL
RAISE = LeducAction.RAISE


def new_game() -> LeducGame:
    return LeducGame()


def deal_private(state: LeducState, p0_card: int, p1_card: int) -> LeducState:
    state = state.apply_action(p0_card)
    return state.apply_action(p1_card)


def deal_public(state: LeducState, card: int) -> LeducState:
    return state.apply_action(card)


ActionSeq = list[LeducAction] | tuple[LeducAction, ...]


def play_round1(state: LeducState, actions: ActionSeq) -> LeducState:
    for action in actions:
        state = state.apply_action(action)
    return state


def play_round2(state: LeducState, public_card: int, actions: ActionSeq) -> LeducState:
    state = deal_public(state, public_card)
    for action in actions:
        state = state.apply_action(action)
    return state


def assert_zero_sum(returns: list[float], tol: float = 1e-9) -> None:
    total = sum(returns)
    assert abs(total) < tol, f"returns not zero-sum: {returns}"
