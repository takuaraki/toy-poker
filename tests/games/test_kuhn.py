"""Tests for Kuhn Poker (2-player)."""

from __future__ import annotations

import itertools

import pytest

from toy_poker.games.kuhn import KuhnAction, KuhnGame, KuhnState

J, Q, K = 0, 1, 2


@pytest.fixture
def game() -> KuhnGame:
    return KuhnGame()


def deal_cards(state: KuhnState, p0_card: int, p1_card: int) -> KuhnState:
    state = state.apply_action(p0_card)
    return state.apply_action(p1_card)


def play_actions(state: KuhnState, actions: list[KuhnAction]) -> KuhnState:
    for action in actions:
        state = state.apply_action(action)
    return state


class TestChanceNode:
    def test_initial_is_chance(self, game: KuhnGame) -> None:
        state = game.new_initial_state()
        assert state.is_chance_node()
        assert not state.is_terminal()
        assert state.legal_actions() == [J, Q, K]

    def test_chance_outcomes_uniform(self, game: KuhnGame) -> None:
        state = game.new_initial_state()
        outcomes = state.chance_outcomes()
        assert len(outcomes) == 3
        assert sum(prob for _, prob in outcomes) == pytest.approx(1.0)

    def test_second_deal_has_two_cards(self, game: KuhnGame) -> None:
        state = game.new_initial_state().apply_action(K)
        assert state.is_chance_node()
        assert state.legal_actions() == [J, Q]


class TestLegalActions:
    def test_player_node_pass_and_bet(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), Q, J)
        assert not state.is_chance_node()
        assert state.current_player() == 0
        assert state.legal_actions() == [KuhnAction.PASS, KuhnAction.BET]


class TestTransitions:
    def test_check_check_showdown(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), Q, J)
        state = play_actions(state, [KuhnAction.PASS, KuhnAction.PASS])
        assert state.is_terminal()
        assert state.winner == 0

    def test_bet_fold(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, J)
        state = play_actions(state, [KuhnAction.BET, KuhnAction.PASS])
        assert state.is_terminal()
        assert state.winner == 0

    def test_pass_bet_fold(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), J, K)
        state = play_actions(state, [KuhnAction.PASS, KuhnAction.BET, KuhnAction.PASS])
        assert state.is_terminal()
        assert state.winner == 1

    def test_bet_call_showdown(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, Q)
        state = play_actions(state, [KuhnAction.BET, KuhnAction.BET])
        assert state.is_terminal()
        assert state.winner == 0

    def test_illegal_chance_action_raises(self, game: KuhnGame) -> None:
        state = game.new_initial_state().apply_action(J)
        with pytest.raises(ValueError, match="illegal chance action"):
            state.apply_action(J)

    def test_illegal_player_action_raises(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), J, Q)
        with pytest.raises(ValueError, match="illegal player action"):
            state.apply_action(99)


class TestPayoffs:
    def test_check_check_winner_plus_one(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, Q)
        state = play_actions(state, [KuhnAction.PASS, KuhnAction.PASS])
        assert state.returns() == [1.0, -1.0]

    def test_bet_fold_winner_plus_one(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), Q, J)
        state = play_actions(state, [KuhnAction.BET, KuhnAction.PASS])
        assert state.returns() == [1.0, -1.0]

    def test_bet_call_showdown_winner_plus_two(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, J)
        state = play_actions(state, [KuhnAction.BET, KuhnAction.BET])
        assert state.returns() == [2.0, -2.0]

    def test_pass_bet_fold(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), J, K)
        state = play_actions(state, [KuhnAction.PASS, KuhnAction.BET, KuhnAction.PASS])
        assert state.returns() == [-1.0, 1.0]


class TestZeroSum:
    def test_all_terminal_states_zero_sum(self, game: KuhnGame) -> None:
        cards = [J, Q, K]
        bet_pass = [KuhnAction.PASS, KuhnAction.BET]
        action_sequences = list(itertools.product(bet_pass, repeat=3))
        action_sequences += [
            (KuhnAction.PASS, KuhnAction.PASS),
            (KuhnAction.PASS, KuhnAction.BET, KuhnAction.PASS),
            (KuhnAction.PASS, KuhnAction.BET, KuhnAction.BET),
            (KuhnAction.BET, KuhnAction.PASS),
            (KuhnAction.BET, KuhnAction.BET),
        ]

        for p0_card, p1_card in itertools.permutations(cards, 2):
            for actions in action_sequences:
                state = deal_cards(game.new_initial_state(), p0_card, p1_card)
                try:
                    state = play_actions(state, list(actions))
                except (ValueError, IndexError):
                    continue
                if not state.is_terminal():
                    continue
                returns = state.returns()
                assert returns[0] + returns[1] == pytest.approx(0.0)


class TestInformationState:
    def test_infostate_matches_openspiel_style(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, Q)
        state = state.apply_action(KuhnAction.BET)
        assert state.information_state_string(0) == "2b"
        assert state.information_state_string(1) == "1b"


class TestActionHistory:
    def test_history_strings(self, game: KuhnGame) -> None:
        state = deal_cards(game.new_initial_state(), K, Q)
        state = play_actions(state, [KuhnAction.BET, KuhnAction.BET])
        assert state.action_history() == [
            "Deal P0: K",
            "Deal P1: Q",
            "P0: Bet",
            "P1: Bet",
        ]
