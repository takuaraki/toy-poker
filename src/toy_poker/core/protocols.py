"""OpenSpiel-style protocols for games, states, and agents."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from toy_poker.core.types import Action, ChanceOutcome, Payoff, PlayerId


@runtime_checkable
class State(Protocol):
    """Immutable game state node."""

    def is_terminal(self) -> bool: ...

    def is_chance_node(self) -> bool: ...

    def current_player(self) -> PlayerId: ...

    def legal_actions(self) -> list[Action]: ...

    def chance_outcomes(self) -> list[ChanceOutcome]: ...

    def apply_action(self, action: Action) -> State: ...

    def returns(self) -> list[Payoff]: ...

    def action_history(self) -> list[str]: ...

    def information_state_string(self, player: PlayerId) -> str: ...


@runtime_checkable
class Game(Protocol):
    """Game definition."""

    def new_initial_state(self) -> State: ...

    def num_players(self) -> int: ...

    def max_utility(self) -> float: ...


@runtime_checkable
class Agent(Protocol):
    """Player strategy."""

    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action: ...
