"""Text formatting for hand histories."""

from __future__ import annotations

from toy_poker.games.kuhn import (
    CARD_NAMES,
    INVALID_PLAYER,
    KuhnAction,
    KuhnState,
)
from toy_poker.runner.hand import HandResult


def format_hand(result: HandResult, *, reveal: bool = True) -> str:
    """Format a completed hand as human-readable text."""
    state = result.final_state
    if isinstance(state, KuhnState):
        return _format_kuhn_hand(state, result.returns, reveal=reveal)
    msg = f"unsupported game state type: {type(state)!r}"
    raise TypeError(msg)


def _format_kuhn_hand(
    state: KuhnState,
    returns: list[float],
    *,
    reveal: bool,
) -> str:
    lines = ["=== Kuhn Poker (2p) ==="]
    lines.extend(_format_kuhn_deal(state, reveal=reveal))
    lines.extend(_format_kuhn_actions(state))
    lines.append(_format_kuhn_outcome(state))
    lines.append(_format_returns(state, returns))
    return "\n".join(lines)


def _format_kuhn_deal(state: KuhnState, *, reveal: bool) -> list[str]:
    cards = [
        _player_card_name(state, player)
        for player in range(state.game.num_players())
    ]
    if reveal:
        deal = f"Deal: P0={cards[0]}, P1={cards[1]}"
    else:
        deal = f"Deal: P0={cards[0]}, P1=?? (hidden)"
    return [deal]


def _format_kuhn_actions(state: KuhnState) -> list[str]:
    lines: list[str] = []
    replay = state.game.new_initial_state()

    for player, action in state.history:
        if player == INVALID_PLAYER:
            replay = replay.apply_action(action)
            continue

        label = kuhn_action_label(replay, player, action)
        lines.append(f"P{player}: {label.upper()}")
        replay = replay.apply_action(action)

    return lines


def kuhn_action_label(state: KuhnState, player: int, action: int) -> str:
    if action == KuhnAction.BET:
        if state.first_bettor == INVALID_PLAYER:
            return "bet"
        return "call"
    if state.first_bettor == INVALID_PLAYER or player == state.first_bettor:
        return "check"
    return "fold"


def _format_kuhn_outcome(state: KuhnState) -> str:
    winner = state.winner
    loser = 1 - winner
    if _is_showdown(state):
        winner_card = CARD_NAMES[state.player_card(winner) or 0]
        loser_card = CARD_NAMES[state.player_card(loser) or 0]
        return f"Showdown: P{winner}={winner_card} beats P{loser}={loser_card}"
    return f"P{loser} folds"


def _is_showdown(state: KuhnState) -> bool:
    if state.first_bettor == INVALID_PLAYER:
        return True
    _, last_action = state.history[-1]
    return last_action == KuhnAction.BET


def _format_returns(state: KuhnState, returns: list[float]) -> str:
    formatted = ", ".join(
        f"P{player}={returns[player]:+.1f}"
        for player in range(state.game.num_players())
    )
    return f"Pot: {state.pot} | Returns: {formatted}"


def _player_card_name(state: KuhnState, player: int) -> str:
    card = state.player_card(player)
    if card is None:
        return "?"
    return CARD_NAMES[card]
