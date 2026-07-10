"""Reproducibility tests with fixed seeds."""

from __future__ import annotations

from toy_poker.agents.human import HumanAgent
from toy_poker.agents.random import RandomAgent
from toy_poker.core.protocols import Agent
from toy_poker.core.rng import make_rng
from toy_poker.games.kuhn import KuhnGame, KuhnState
from toy_poker.games.leduc import LeducGame, LeducState
from toy_poker.runner.hand import run_hand, run_match


def test_make_rng_same_seed_same_draws() -> None:
    assert make_rng(7).integers(1000) == make_rng(7).integers(1000)


def test_run_hand_identical_with_same_seed() -> None:
    game = KuhnGame()

    def play(seed: int) -> tuple[list[float], list[str], int]:
        rng = make_rng(seed)
        agents = [RandomAgent(rng), RandomAgent(rng)]
        result = run_hand(game, agents, rng)
        assert isinstance(result.final_state, KuhnState)
        return (
            result.returns,
            result.final_state.action_history(),
            result.final_state.pot,
        )

    assert play(42) == play(42)
    assert play(42) != play(99)


def test_run_match_identical_with_same_seed() -> None:
    game = KuhnGame()

    def play(seed: int) -> list[list[float]]:
        rng = make_rng(seed)
        agents = [RandomAgent(rng), RandomAgent(rng)]
        match = run_match(game, agents, num_hands=5, rng=rng)
        return [hand.returns for hand in match.hand_results]

    assert play(0) == play(0)
    assert play(0) != play(1)


def test_human_agent_full_hand_reproducible_with_mock_input() -> None:
    """Human plays check-check; opponent randomness fixed by seed."""
    game = KuhnGame()
    rng = make_rng(5)
    human = HumanAgent(
        player_id=0,
        input_fn=lambda _: "1",  # always pick first legal action
        output_fn=lambda _: None,
    )
    agents: list[Agent] = [human, RandomAgent(rng)]

    result = run_hand(game, agents, rng)
    assert result.final_state.is_terminal()
    assert result.returns[0] + result.returns[1] == 0.0


def test_leduc_run_hand_identical_with_same_seed() -> None:
    game = LeducGame()

    def play(seed: int) -> tuple[list[float], list[str], int]:
        rng = make_rng(seed)
        agents = [RandomAgent(rng), RandomAgent(rng)]
        result = run_hand(game, agents, rng)
        assert isinstance(result.final_state, LeducState)
        return (
            result.returns,
            result.final_state.action_history(),
            result.final_state.pot,
        )

    assert play(42) == play(42)
    assert play(42) != play(99)


def test_leduc_human_agent_full_hand_with_mock_input() -> None:
    game = LeducGame()
    rng = make_rng(5)
    human = HumanAgent(
        player_id=0,
        input_fn=lambda _: "1",
        output_fn=lambda _: None,
    )
    agents: list[Agent] = [human, RandomAgent(rng)]
    result = run_hand(game, agents, rng)
    assert result.final_state.is_terminal()
    assert abs(result.returns[0] + result.returns[1]) < 1e-9
