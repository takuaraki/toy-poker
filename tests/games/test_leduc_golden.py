"""Golden-path payoff checks for Leduc Hold'em."""

from __future__ import annotations

import pytest

from tests.games.leduc_helpers import (
    CALL,
    FOLD,
    JS,
    KH,
    KS,
    QH,
    QS,
    RAISE,
    assert_zero_sum,
    deal_private,
    new_game,
    play_round1,
    play_round2,
)


@pytest.mark.parametrize(
    ("p0", "p1", "r1", "public", "r2", "expected_winner", "expected_returns"),
    [
        # K-high beats J-high when board does not pair either card
        (KS, JS, (CALL, CALL), QH, (CALL, CALL), 0, [1.0, -1.0]),
        # P0 raises, P1 folds
        (QS, QH, (RAISE, FOLD), None, (), 0, [1.0, -1.0]),
        # P0 raises, P1 calls, check-check round 2, pair wins
        (KS, JS, (RAISE, CALL), KH, (CALL, CALL), 0, [3.0, -3.0]),
        # Regression: Queen pair beats King high (user-reported showdown bug)
        (KS, QS, (CALL, CALL), QH, (CALL, CALL), 1, [-1.0, 1.0]),
        # Split pot: both King-high (Ks vs Kh, board Jack)
        (KS, KH, (CALL, CALL), JS, (CALL, CALL), 0, [0.0, 0.0]),
        # Kicker: Qs beats Js when both King-high on Kh
        (JS, QS, (CALL, CALL), KH, (CALL, CALL), 1, [-1.0, 1.0]),
        # Fold to re-raise in round 1
        (KS, JS, (RAISE, RAISE, FOLD), None, (), 1, [-3.0, 3.0]),
        # Check-raise-fold in round 1
        (KS, JS, (CALL, RAISE, FOLD), None, (), 1, [-1.0, 1.0]),
        # Round 2 fold after P0 raise
        (KS, JS, (CALL, CALL), QH, (RAISE, FOLD), 0, [1.0, -1.0]),
        # Round 2 check-raise-fold
        (KS, JS, (CALL, CALL), QH, (CALL, RAISE, FOLD), 1, [-1.0, 1.0]),
        # Max raises both rounds, K-high wins
        (KS, JS, (RAISE, RAISE, CALL), QH, (RAISE, RAISE, CALL), 0, [13.0, -13.0]),
    ],
)
def test_golden_paths(
    p0: int,
    p1: int,
    r1: tuple,
    public: int | None,
    r2: tuple,
    expected_winner: int,
    expected_returns: list[float],
) -> None:
    state = deal_private(new_game().new_initial_state(), p0, p1)
    state = play_round1(state, r1)
    if public is not None:
        state = play_round2(state, public, r2)
    assert state.is_terminal()
    assert state.winner == expected_winner
    assert state.returns() == pytest.approx(expected_returns)
    assert_zero_sum(state.returns())
