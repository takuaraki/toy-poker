"""Golden-path payoff checks for Leduc Hold'em."""

from __future__ import annotations

import pytest

from tests.games.leduc_helpers import (
    CALL,
    FOLD,
    JH,
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
        # check-check, check-check showdown: higher private wins (K > J)
        (KS, JS, (CALL, CALL), JH, (CALL, CALL), 0, [1.0, -1.0]),
        # P0 raises, P1 folds
        (QS, QH, (RAISE, FOLD), None, (), 0, [1.0, -1.0]),
        # P0 raises, P1 calls, check-check round 2, pair wins
        (KS, JS, (RAISE, CALL), KH, (CALL, CALL), 0, [3.0, -3.0]),
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
