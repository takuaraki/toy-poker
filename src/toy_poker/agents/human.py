"""Human player agent via CLI input."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from toy_poker.core.protocols import Agent, State
from toy_poker.core.types import Action, PlayerId
from toy_poker.games.kuhn import CARD_NAMES, INVALID_PLAYER, KuhnState
from toy_poker.runner.format import kuhn_action_label


@dataclass
class HumanAgent:
    """Prompts a human player to choose an action from stdin."""

    player_id: PlayerId
    input_fn: Callable[[str], str] = input
    output_fn: Callable[[str], None] = print

    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action:
        if player != self.player_id:
            msg = f"HumanAgent for P{self.player_id} cannot act for P{player}"
            raise ValueError(msg)
        if not isinstance(state, KuhnState):
            msg = f"HumanAgent supports KuhnState only, got {type(state)!r}"
            raise TypeError(msg)

        self._print_turn(state, player)
        return self._read_action(state, player, legal_actions)

    def _print_turn(self, state: KuhnState, player: PlayerId) -> None:
        card = state.player_card(player)
        card_name = CARD_NAMES[card] if card is not None else "?"
        self.output_fn(f"\n--- Your turn (P{player}) ---")
        self.output_fn(f"Your card: {card_name}")
        self.output_fn(f"History: {_format_betting_history(state)}")

    def _read_action(
        self,
        state: KuhnState,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action:
        while True:
            self.output_fn("Legal actions:")
            for index, action in enumerate(legal_actions, start=1):
                label = kuhn_action_label(state, player, action).upper()
                self.output_fn(f"  [{index}] {label}")
            raw = self.input_fn("> ").strip()
            try:
                choice = int(raw)
            except ValueError:
                self.output_fn("Invalid input. Enter a number from the menu.")
                continue
            if 1 <= choice <= len(legal_actions):
                return legal_actions[choice - 1]
            self.output_fn(
                f"Invalid choice. Enter a number between 1 and {len(legal_actions)}."
            )


@dataclass
class AnnouncingAgent:
    """Wraps an agent and announces its action to the console."""

    agent: Agent
    player_id: PlayerId
    output_fn: Callable[[str], None] = print

    def select_action(
        self,
        state: State,
        player: PlayerId,
        legal_actions: list[Action],
    ) -> Action:
        action = self.agent.select_action(state, player, legal_actions)
        if isinstance(state, KuhnState):
            label = kuhn_action_label(state, player, action).upper()
            self.output_fn(f"P{player}: {label}")
        return action


def _format_betting_history(state: KuhnState) -> str:
    if len(state.history) <= state.game.num_players():
        return "(none)"

    replay = state.game.new_initial_state()
    events: list[str] = []
    for actor, action in state.history:
        if actor == INVALID_PLAYER:
            replay = replay.apply_action(action)
            continue
        label = kuhn_action_label(replay, actor, action).upper()
        events.append(f"P{actor}: {label}")
        replay = replay.apply_action(action)
    return ", ".join(events)
