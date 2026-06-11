"""Kuhn Poker (2-player), OpenSpiel-compatible formulation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Final

from toy_poker.core.state import (
    check_chance_node,
    check_not_terminal,
    check_player_node,
)
from toy_poker.core.types import Action, ChanceOutcome, Payoff, PlayerId

INVALID_PLAYER: Final = -1
CHANCE_PLAYER: Final = -1

CARD_NAMES: Final = ("J", "Q", "K")


class KuhnAction(IntEnum):
    """Player actions (OpenSpiel: Pass=0, Bet=1)."""

    PASS = 0
    BET = 1


@dataclass(frozen=True)
class KuhnGame:
    """Two-player Kuhn Poker."""

    ante: int = 1
    bet_size: int = 1

    def num_players(self) -> int:
        return 2

    def new_initial_state(self) -> KuhnState:
        n = self.num_players()
        return KuhnState(
            game=self,
            card_dealt=tuple(INVALID_PLAYER for _ in range(n + 1)),
            history=(),
            first_bettor=INVALID_PLAYER,
            winner=INVALID_PLAYER,
            pot=self.ante * n,
            contributions=tuple(self.ante for _ in range(n)),
        )

    def max_utility(self) -> float:
        return float((self.num_players() - 1) * 2)


@dataclass(frozen=True)
class KuhnState:
    """Immutable Kuhn Poker state (OpenSpiel-compatible)."""

    game: KuhnGame
    card_dealt: tuple[int, ...]
    history: tuple[tuple[int, Action], ...]
    first_bettor: int
    winner: int
    pot: int
    contributions: tuple[int, ...]

    def is_terminal(self) -> bool:
        return self.winner != INVALID_PLAYER

    def is_chance_node(self) -> bool:
        return not self.is_terminal() and len(self.history) < self.game.num_players()

    def current_player(self) -> PlayerId:
        if self.is_terminal():
            msg = "current_player() is undefined on terminal states"
            raise ValueError(msg)
        if self.is_chance_node():
            msg = "current_player() is undefined on chance nodes"
            raise ValueError(msg)
        return len(self.history) % self.game.num_players()

    def legal_actions(self) -> list[Action]:
        if self.is_terminal():
            return []
        if self.is_chance_node():
            return [
                card
                for card, owner in enumerate(self.card_dealt)
                if owner == INVALID_PLAYER
            ]
        return [KuhnAction.PASS, KuhnAction.BET]

    def chance_outcomes(self) -> list[ChanceOutcome]:
        check_chance_node(self)
        legal = self.legal_actions()
        probability = 1.0 / len(legal)
        return [(action, probability) for action in legal]

    def apply_action(self, action: Action) -> KuhnState:
        check_not_terminal(self)
        if self.is_chance_node():
            return self._apply_chance_action(action)
        return self._apply_player_action(action)

    def returns(self) -> list[Payoff]:
        if not self.is_terminal():
            msg = "returns() is only defined on terminal states"
            raise ValueError(msg)

        result: list[Payoff] = []
        for player in range(self.game.num_players()):
            contribution = 2 if self._did_bet(player) else 1
            if player == self.winner:
                result.append(float(self.pot - contribution))
            else:
                result.append(float(-contribution))
        return result

    def action_history(self) -> list[str]:
        lines: list[str] = []
        for index, (player, move) in enumerate(self.history):
            if index < self.game.num_players():
                deal_player = index
                card_name = CARD_NAMES[move]
                lines.append(f"Deal P{deal_player}: {card_name}")
            else:
                action_name = "Bet" if move == KuhnAction.BET else "Pass"
                lines.append(f"P{player}: {action_name}")
        return lines

    def information_state_string(self, player: PlayerId) -> str:
        if player < 0 or player >= self.game.num_players():
            msg = f"invalid player id: {player}"
            raise ValueError(msg)
        if len(self.history) <= player:
            msg = "card has not been dealt to this player yet"
            raise ValueError(msg)

        card = self.history[player][1]
        betting = "".join(
            "b" if move == KuhnAction.BET else "p"
            for deal_player, move in self.history[self.game.num_players() :]
        )
        return f"{card}{betting}"

    def player_card(self, player: PlayerId) -> int | None:
        if len(self.history) <= player:
            return None
        return self.history[player][1]

    def _apply_chance_action(self, action: Action) -> KuhnState:
        check_chance_node(self)
        legal = self.legal_actions()
        if action not in legal:
            msg = f"illegal chance action: {action}"
            raise ValueError(msg)

        deal_to = len(self.history)
        card_dealt = list(self.card_dealt)
        card_dealt[action] = deal_to
        history = self.history + ((CHANCE_PLAYER, action),)
        return replace(self, card_dealt=tuple(card_dealt), history=history)

    def _apply_player_action(self, action: Action) -> KuhnState:
        check_player_node(self)
        if action not in (KuhnAction.PASS, KuhnAction.BET):
            msg = f"illegal player action: {action}"
            raise ValueError(msg)

        player = self.current_player()
        first_bettor = self.first_bettor
        pot = self.pot
        contributions = list(self.contributions)

        if action == KuhnAction.BET:
            if first_bettor == INVALID_PLAYER:
                first_bettor = player
            pot += self.game.bet_size
            contributions[player] += self.game.bet_size

        history = self.history + ((player, action),)
        state = replace(
            self,
            history=history,
            first_bettor=first_bettor,
            pot=pot,
            contributions=tuple(contributions),
        )
        winner = state._resolve_winner()
        return replace(state, winner=winner)

    def _resolve_winner(self) -> int:
        num_players = self.game.num_players()
        num_actions = len(self.history) - num_players

        if self.first_bettor == INVALID_PLAYER and num_actions == num_players:
            return self._showdown_winner_no_bets()

        betting_complete = num_actions == num_players + self.first_bettor
        if self.first_bettor != INVALID_PLAYER and betting_complete:
            return self._showdown_winner_with_bets()

        return INVALID_PLAYER

    def _showdown_winner_no_bets(self) -> int:
        num_cards = self.game.num_players() + 1
        for card in range(num_cards - 1, -1, -1):
            player = self.card_dealt[card]
            if player != INVALID_PLAYER:
                return player
        msg = "no player holds a card"
        raise RuntimeError(msg)

    def _showdown_winner_with_bets(self) -> int:
        num_cards = self.game.num_players() + 1
        for card in range(num_cards - 1, -1, -1):
            player = self.card_dealt[card]
            if player != INVALID_PLAYER and self._did_bet(player):
                return player
        msg = "no eligible winner after betting"
        raise RuntimeError(msg)

    def _did_bet(self, player: PlayerId) -> bool:
        if self.first_bettor == INVALID_PLAYER:
            return False
        if player == self.first_bettor:
            return True

        num_players = self.game.num_players()
        if player > self.first_bettor:
            history_index = num_players + player
        else:
            history_index = num_players * 2 + player

        _, action = self.history[history_index]
        return action == KuhnAction.BET
