"""Shared state validation helpers."""

from __future__ import annotations

from toy_poker.core.protocols import State


def check_not_terminal(state: State) -> None:
    """Raise if the state is terminal."""
    if state.is_terminal():
        msg = "Operation invalid on terminal state"
        raise ValueError(msg)


def check_chance_node(state: State) -> None:
    """Raise if the state is not a chance node."""
    if not state.is_chance_node():
        msg = "Operation requires a chance node"
        raise ValueError(msg)


def check_player_node(state: State) -> None:
    """Raise if the state is not a player decision node."""
    check_not_terminal(state)
    if state.is_chance_node():
        msg = "Operation requires a player node"
        raise ValueError(msg)
