"""Hand and match execution."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from toy_poker.core.protocols import Agent, Game, State
from toy_poker.core.types import Payoff


@dataclass(frozen=True)
class HandResult:
    """Outcome of a single hand."""

    returns: list[Payoff]
    final_state: State


@dataclass(frozen=True)
class MatchResult:
    """Outcome of multiple hands."""

    mean_returns: list[float]
    std_returns: list[float]
    hand_results: tuple[HandResult, ...]

    @property
    def num_hands(self) -> int:
        return len(self.hand_results)


def run_hand(
    game: Game,
    agents: Sequence[Agent],
    rng: np.random.Generator,
) -> HandResult:
    """Play one hand to completion."""
    state = game.new_initial_state()
    while not state.is_terminal():
        if state.is_chance_node():
            outcomes = state.chance_outcomes()
            actions, probabilities = zip(*outcomes, strict=True)
            action = int(rng.choice(actions, p=probabilities))
        else:
            player = state.current_player()
            legal_actions = state.legal_actions()
            action = agents[player].select_action(state, player, legal_actions)
        state = state.apply_action(action)
    return HandResult(returns=state.returns(), final_state=state)


def run_match(
    game: Game,
    agents: Sequence[Agent],
    num_hands: int,
    rng: np.random.Generator,
) -> MatchResult:
    """Play multiple hands using one shared RNG stream."""
    hand_results: list[HandResult] = []
    for _ in range(num_hands):
        hand_results.append(run_hand(game, agents, rng))

    returns_matrix = np.array([result.returns for result in hand_results])
    mean_returns = returns_matrix.mean(axis=0).tolist()
    std_returns = returns_matrix.std(axis=0).tolist()
    return MatchResult(
        mean_returns=mean_returns,
        std_returns=std_returns,
        hand_results=tuple(hand_results),
    )
