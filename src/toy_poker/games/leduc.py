"""Leduc Hold'em (2-player), OpenSpiel-compatible formulation."""

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
INVALID_CARD: Final = -1
CHANCE_PLAYER: Final = -1

# 0=Js, 1=Jh, 2=Qs, 3=Qh, 4=Ks, 5=Kh (OpenSpiel 2-player deck order)
CARD_NAMES: Final = ("Js", "Jh", "Qs", "Qh", "Ks", "Kh")
NUM_SUITS: Final = 2


class LeducAction(IntEnum):
    """Player actions (OpenSpiel: Fold=0, Call=1, Raise=2)."""

    FOLD = 0
    CALL = 1
    RAISE = 2


@dataclass(frozen=True)
class LeducGame:
    """Two-player Leduc Hold'em."""

    ante: int = 1
    first_raise_amount: int = 2
    second_raise_amount: int = 4
    max_raises_per_round: int = 2
    starting_player: int = 0

    def num_players(self) -> int:
        return 2

    def num_cards(self) -> int:
        return (self.num_players() + 1) * NUM_SUITS

    def raise_amount(self, round_number: int) -> int:
        if round_number == 1:
            return self.first_raise_amount
        if round_number == 2:
            return self.second_raise_amount
        msg = f"invalid round: {round_number}"
        raise ValueError(msg)

    def new_initial_state(self) -> LeducState:
        n = self.num_players()
        num_cards = self.num_cards()
        return LeducState(
            game=self,
            deck=tuple(range(num_cards)),
            private_cards=tuple(INVALID_CARD for _ in range(n)),
            public_card=INVALID_CARD,
            round_number=1,
            pot=self.ante * n,
            stakes=self.ante,
            contributions=tuple(self.ante for _ in range(n)),
            folded=tuple(False for _ in range(n)),
            num_calls=0,
            num_raises=0,
            cur_player=CHANCE_PLAYER,
            private_cards_dealt=0,
            round1_sequence=(),
            round2_sequence=(),
            winner=INVALID_PLAYER,
            winners=tuple(False for _ in range(n)),
        )

    def max_utility(self) -> float:
        per_round = self.max_raises_per_round * (
            self.first_raise_amount + self.second_raise_amount
        )
        return float((self.num_players() - 1) * (per_round + 1))


@dataclass(frozen=True)
class LeducState:
    """Immutable Leduc Hold'em state (OpenSpiel-compatible)."""

    game: LeducGame
    deck: tuple[int, ...]
    private_cards: tuple[int, ...]
    public_card: int
    round_number: int
    pot: int
    stakes: int
    contributions: tuple[int, ...]
    folded: tuple[bool, ...]
    num_calls: int
    num_raises: int
    cur_player: int
    private_cards_dealt: int
    round1_sequence: tuple[Action, ...]
    round2_sequence: tuple[Action, ...]
    winner: int
    winners: tuple[bool, ...]

    def is_terminal(self) -> bool:
        return self.winner != INVALID_PLAYER

    def is_chance_node(self) -> bool:
        return not self.is_terminal() and self.cur_player == CHANCE_PLAYER

    def current_player(self) -> PlayerId:
        if self.is_terminal():
            msg = "current_player() is undefined on terminal states"
            raise ValueError(msg)
        if self.is_chance_node():
            msg = "current_player() is undefined on chance nodes"
            raise ValueError(msg)
        return self.cur_player

    def legal_actions(self) -> list[Action]:
        if self.is_terminal():
            return []
        if self.is_chance_node():
            return [card for card in self.deck if card != INVALID_CARD]
        actions: list[Action] = [LeducAction.CALL]
        if self.stakes > self.contributions[self.cur_player]:
            actions.insert(0, LeducAction.FOLD)
        if self.num_raises < self.game.max_raises_per_round:
            actions.append(LeducAction.RAISE)
        return actions

    def chance_outcomes(self) -> list[ChanceOutcome]:
        check_chance_node(self)
        legal = self.legal_actions()
        probability = 1.0 / len(legal)
        return [(action, probability) for action in legal]

    def apply_action(self, action: Action) -> LeducState:
        check_not_terminal(self)
        if self.is_chance_node():
            return self._apply_chance_action(action)
        return self._apply_player_action(action)

    def returns(self) -> list[Payoff]:
        if not self.is_terminal():
            msg = "returns() is only defined on terminal states"
            raise ValueError(msg)

        payouts = [0.0, 0.0]
        num_winners = sum(self.winners)
        if num_winners == 1:
            winner = next(i for i, won in enumerate(self.winners) if won)
            payouts[winner] = float(self.pot)
        elif num_winners > 1:
            share = self.pot / num_winners
            for player, won in enumerate(self.winners):
                if won:
                    payouts[player] = float(share)

        return [
            payout - self.contributions[player]
            for player, payout in enumerate(payouts)
        ]

    def action_history(self) -> list[str]:
        lines: list[str] = []
        for player in range(self.game.num_players()):
            card = self.private_cards[player]
            if card != INVALID_CARD:
                lines.append(f"Deal P{player}: {CARD_NAMES[card]}")
        if self.public_card != INVALID_CARD:
            lines.append(f"Deal public: {CARD_NAMES[self.public_card]}")
        for action in self.round1_sequence:
            lines.append(f"R1: {_action_name(action)}")
        for action in self.round2_sequence:
            lines.append(f"R2: {_action_name(action)}")
        return lines

    def information_state_string(self, player: PlayerId) -> str:
        if player < 0 or player >= self.game.num_players():
            msg = f"invalid player id: {player}"
            raise ValueError(msg)
        card = self.private_cards[player]
        if card == INVALID_CARD:
            msg = "card has not been dealt to this player yet"
            raise ValueError(msg)
        public = "x" if self.public_card == INVALID_CARD else str(self.public_card)
        r1 = "".join(_action_char(action) for action in self.round1_sequence)
        r2 = "".join(_action_char(action) for action in self.round2_sequence)
        return f"{card}|{public}|{r1}|{r2}"

    def player_card(self, player: PlayerId) -> int | None:
        card = self.private_cards[player]
        return None if card == INVALID_CARD else card

    def remaining_players(self) -> int:
        return sum(not folded for folded in self.folded)

    def _apply_chance_action(self, action: Action) -> LeducState:
        check_chance_node(self)
        if action not in self.legal_actions():
            msg = f"illegal chance action: {action}"
            raise ValueError(msg)

        deck = list(self.deck)
        deck[action] = INVALID_CARD

        if self.private_cards_dealt < self.game.num_players():
            private_cards = list(self.private_cards)
            private_cards[self.private_cards_dealt] = action
            dealt = self.private_cards_dealt + 1
            cur_player = (
                self.game.starting_player
                if dealt == self.game.num_players()
                else CHANCE_PLAYER
            )
            return replace(
                self,
                deck=tuple(deck),
                private_cards=tuple(private_cards),
                private_cards_dealt=dealt,
                cur_player=cur_player,
            )

        return replace(
            self,
            deck=tuple(deck),
            public_card=action,
            cur_player=self._next_player(self.game.starting_player - 1),
        )

    def _apply_player_action(self, action: Action) -> LeducState:
        check_player_node(self)
        if action not in self.legal_actions():
            msg = f"illegal player action: {action}"
            raise ValueError(msg)

        player = self.cur_player
        state = self

        if action == LeducAction.FOLD:
            folded = list(state.folded)
            folded[player] = True
            state = replace(state, folded=tuple(folded))
            state = state._record_action(LeducAction.FOLD)
        elif action == LeducAction.CALL:
            amount = state.stakes - state.contributions[player]
            state = state._ante(player, amount)
            state = replace(state, num_calls=state.num_calls + 1)
            state = state._record_action(LeducAction.CALL)
        else:
            call_amount = state.stakes - state.contributions[player]
            if call_amount > 0:
                state = state._ante(player, call_amount)
            raise_amount = state.game.raise_amount(state.round_number)
            state = state._ante(player, raise_amount)
            state = replace(
                state,
                stakes=state.stakes + raise_amount,
                num_raises=state.num_raises + 1,
                num_calls=0,
            )
            state = state._record_action(LeducAction.RAISE)

        return state._advance_after_action()

    def _record_action(self, action: Action) -> LeducState:
        if self.round_number == 1:
            return replace(self, round1_sequence=self.round1_sequence + (action,))
        return replace(self, round2_sequence=self.round2_sequence + (action,))

    def _ante(self, player: int, amount: int) -> LeducState:
        if amount < 0:
            msg = f"negative ante amount: {amount}"
            raise ValueError(msg)
        contributions = list(self.contributions)
        contributions[player] += amount
        return replace(
            self,
            pot=self.pot + amount,
            contributions=tuple(contributions),
        )

    def _advance_after_action(self) -> LeducState:
        if self.remaining_players() == 1:
            return self._resolve_winner()
        if self._ready_for_next_round():
            if self.round_number == 2:
                return self._resolve_winner()
            return self._start_round_two()
        return replace(self, cur_player=self._next_player(self.cur_player))

    def _ready_for_next_round(self) -> bool:
        remaining = self.remaining_players()
        if self.num_raises == 0:
            return self.num_calls == remaining
        return self.num_calls == remaining - 1

    def _start_round_two(self) -> LeducState:
        return replace(
            self,
            round_number=2,
            num_raises=0,
            num_calls=0,
            cur_player=CHANCE_PLAYER,
        )

    def _resolve_winner(self) -> LeducState:
        if self.remaining_players() == 1:
            winners = tuple(not folded for folded in self.folded)
            winner = winners.index(True)
            return replace(self, winner=winner, winners=winners)

        ranks = [
            self._rank_hand(player) if not folded else -1
            for player, folded in enumerate(self.folded)
        ]
        best = max(rank for rank in ranks if rank >= 0)
        winners = tuple(rank == best for rank in ranks)
        winner = winners.index(True)
        return replace(self, winner=winner, winners=winners)

    def _rank_hand(self, player: int) -> int:
        hand = sorted((self.public_card, self.private_cards[player]))
        low, high = hand
        num_cards = self.game.num_cards()

        if high % NUM_SUITS == 0 and high == low + 1:
            return num_cards * num_cards + low
        return (high // NUM_SUITS) * num_cards + (low // NUM_SUITS)

    def _next_player(self, from_player: int) -> int:
        n = self.game.num_players()
        for offset in range(1, n + 1):
            player = (from_player + offset) % n
            if not self.folded[player]:
                return player
        msg = "no active player found"
        raise RuntimeError(msg)


def _action_name(action: Action) -> str:
    if action == LeducAction.FOLD:
        return "Fold"
    if action == LeducAction.RAISE:
        return "Raise"
    return "Call"


def _action_char(action: Action) -> str:
    if action == LeducAction.FOLD:
        return "f"
    if action == LeducAction.RAISE:
        return "r"
    return "c"
