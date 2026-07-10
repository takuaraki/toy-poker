"""Text formatting for hand histories."""

from __future__ import annotations

from toy_poker.games.kuhn import (
    CARD_NAMES as KUHN_CARD_NAMES,
)
from toy_poker.games.kuhn import (
    INVALID_PLAYER,
    KuhnAction,
    KuhnState,
)
from toy_poker.games.leduc import (
    CARD_NAMES as LEDUC_CARD_NAMES,
)
from toy_poker.games.leduc import (
    INVALID_CARD,
    LeducAction,
    LeducState,
)
from toy_poker.runner.hand import HandResult


def format_hand(result: HandResult, *, reveal: bool = True) -> str:
    """Format a completed hand as human-readable text."""
    state = result.final_state
    if isinstance(state, KuhnState):
        return _format_kuhn_hand(state, result.returns, reveal=reveal)
    if isinstance(state, LeducState):
        return _format_leduc_hand(state, result.returns, reveal=reveal)
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
    lines.append(_format_returns(state.pot, state.game.num_players(), returns))
    return "\n".join(lines)


def _format_kuhn_deal(state: KuhnState, *, reveal: bool) -> list[str]:
    cards = [
        _kuhn_card_name(state, player)
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
    if _is_kuhn_showdown(state):
        winner_card = KUHN_CARD_NAMES[state.player_card(winner) or 0]
        loser_card = KUHN_CARD_NAMES[state.player_card(loser) or 0]
        return f"Showdown: P{winner}={winner_card} beats P{loser}={loser_card}"
    return f"P{loser} folds"


def _is_kuhn_showdown(state: KuhnState) -> bool:
    if state.first_bettor == INVALID_PLAYER:
        return True
    _, last_action = state.history[-1]
    return last_action == KuhnAction.BET


def _format_leduc_hand(
    state: LeducState,
    returns: list[float],
    *,
    reveal: bool,
) -> str:
    lines = ["=== Leduc Hold'em (2p) ==="]
    lines.extend(_format_leduc_deal(state, reveal=reveal))
    lines.extend(_format_leduc_actions(state))
    lines.append(_format_leduc_outcome(state))
    lines.append(_format_returns(state.pot, state.game.num_players(), returns))
    return "\n".join(lines)


def _format_leduc_deal(state: LeducState, *, reveal: bool) -> list[str]:
    cards = [
        _leduc_card_name(state.player_card(player))
        for player in range(state.game.num_players())
    ]
    if reveal:
        return [f"Deal: P0={cards[0]}, P1={cards[1]}"]
    return [f"Deal: P0={cards[0]}, P1=?? (hidden)"]


def _format_leduc_actions(state: LeducState) -> list[str]:
    lines: list[str] = []
    replay = state.game.new_initial_state()

    # Private deals
    for card in state.private_cards:
        if card == INVALID_CARD:
            break
        replay = replay.apply_action(card)

    for action in state.round1_sequence:
        player = replay.current_player()
        label = leduc_action_label(replay, player, action)
        lines.append(f"R1 P{player}: {label.upper()}")
        replay = replay.apply_action(action)

    if state.public_card != INVALID_CARD:
        lines.append(f"Public: {_leduc_card_name(state.public_card)}")
        replay = replay.apply_action(state.public_card)

    for action in state.round2_sequence:
        player = replay.current_player()
        label = leduc_action_label(replay, player, action)
        lines.append(f"R2 P{player}: {label.upper()}")
        replay = replay.apply_action(action)

    return lines


def leduc_action_label(state: LeducState, player: int, action: int) -> str:
    if action == LeducAction.FOLD:
        return "fold"
    if action == LeducAction.RAISE:
        return "raise"
    if state.stakes > state.contributions[player]:
        return "call"
    return "check"


def _format_leduc_outcome(state: LeducState) -> str:
    if any(state.folded):
        loser = state.folded.index(True)
        return f"P{loser} folds"

    board = _leduc_card_name(state.public_card)
    winners = [player for player, won in enumerate(state.winners) if won]
    if len(winners) > 1:
        names = ", ".join(
            f"P{player}={_leduc_card_name(state.player_card(player))}"
            for player in winners
        )
        return f"Showdown: split pot ({names}; board={board})"

    winner = winners[0]
    loser = 1 - winner
    winner_card = _leduc_card_name(state.player_card(winner))
    loser_card = _leduc_card_name(state.player_card(loser))
    return (
        f"Showdown: P{winner}={winner_card} beats P{loser}={loser_card}"
        f" (board={board})"
    )


def _format_returns(pot: int, num_players: int, returns: list[float]) -> str:
    formatted = ", ".join(
        f"P{player}={returns[player]:+.1f}" for player in range(num_players)
    )
    return f"Pot: {pot} | Returns: {formatted}"


def _kuhn_card_name(state: KuhnState, player: int) -> str:
    card = state.player_card(player)
    if card is None:
        return "?"
    return KUHN_CARD_NAMES[card]


def _leduc_card_name(card: int | None) -> str:
    if card is None or card == INVALID_CARD:
        return "?"
    return LEDUC_CARD_NAMES[card]
