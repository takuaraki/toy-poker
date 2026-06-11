"""Shared helpers for Kuhn game tests."""

from __future__ import annotations

import itertools

from toy_poker.games.kuhn import KuhnAction, KuhnGame, KuhnState

J, Q, K = 0, 1, 2
CARDS = (J, Q, K)

CHECK = KuhnAction.PASS
FOLD = KuhnAction.PASS
BET = KuhnAction.BET
CALL = KuhnAction.BET

TERMINAL_PATHS: tuple[tuple[KuhnAction, ...], ...] = (
    (CHECK, CHECK),
    (CHECK, BET, FOLD),
    (CHECK, BET, CALL),
    (BET, FOLD),
    (BET, CALL),
)


def deal_cards(state: KuhnState, p0_card: int, p1_card: int) -> KuhnState:
    state = state.apply_action(p0_card)
    return state.apply_action(p1_card)


ActionSeq = list[KuhnAction] | tuple[KuhnAction, ...]


def play_actions(state: KuhnState, actions: ActionSeq) -> KuhnState:
    for action in actions:
        state = state.apply_action(action)
    return state


def all_card_deals() -> list[tuple[int, int]]:
    return list(itertools.permutations(CARDS, 2))


def reference_outcome(
    p0_card: int,
    p1_card: int,
    actions: tuple[KuhnAction, ...],
) -> tuple[int, list[float], int]:
    """Independent reference for golden tests (ante=1, bet=1)."""
    ante = 1
    bet = 1
    pot = 2 * ante

    if actions == (CHECK, CHECK):
        winner = 0 if p0_card > p1_card else 1
        returns = [1.0, -1.0] if winner == 0 else [-1.0, 1.0]
        return winner, returns, pot

    if actions == (BET, FOLD):
        pot += bet
        return 0, [1.0, -1.0], pot

    if actions == (CHECK, BET, FOLD):
        pot += bet
        return 1, [-1.0, 1.0], pot

    if actions in ((BET, CALL), (CHECK, BET, CALL)):
        pot += 2 * bet
        winner = 0 if p0_card > p1_card else 1
        returns = [2.0, -2.0] if winner == 0 else [-2.0, 2.0]
        return winner, returns, pot

    msg = f"unknown terminal path: {actions}"
    raise ValueError(msg)


def new_game() -> KuhnGame:
    return KuhnGame()
