"""Leduc Hold'em CLI demo."""

from __future__ import annotations

import argparse
import sys

import numpy as np

from toy_poker.agents.human import AnnouncingAgent, HumanAgent
from toy_poker.agents.random import RandomAgent
from toy_poker.core.protocols import Agent
from toy_poker.core.rng import make_rng
from toy_poker.games.leduc import LeducGame
from toy_poker.runner.format import format_hand
from toy_poker.runner.hand import run_hand, run_match


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play Leduc Hold'em (2-player)")
    parser.add_argument(
        "--hands",
        type=int,
        default=1,
        help="number of hands to play (default: 1)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="random seed (default: 42)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="print summary only (no per-hand history)",
    )
    parser.add_argument(
        "--human",
        action="store_true",
        help="play one hand against a random AI",
    )
    parser.add_argument(
        "--seat",
        type=int,
        default=0,
        choices=[0, 1],
        help="seat when using --human (default: 0)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.hands < 1:
        parser.error("--hands must be at least 1")
    if args.human and args.hands != 1:
        parser.error("--human mode supports exactly one hand")
    if args.human and args.quiet:
        parser.error("--human cannot be combined with --quiet")

    game = LeducGame()
    rng = make_rng(args.seed)

    if args.human:
        _play_human_game(game, rng, human_seat=args.seat)
        return

    agents = [RandomAgent(rng), RandomAgent(rng)]
    if args.hands == 1:
        result = run_hand(game, agents, rng)
        if not args.quiet:
            print(format_hand(result))
            print()
        _print_returns(result.returns)
        return

    match = run_match(game, agents, num_hands=args.hands, rng=rng)
    if not args.quiet:
        for index, hand_result in enumerate(match.hand_results, start=1):
            print(f"--- Hand {index} ---")
            print(format_hand(hand_result))
            print()

    print(f"Played {match.num_hands} hands (seed={args.seed})")
    for player, mean in enumerate(match.mean_returns):
        std = match.std_returns[player]
        print(f"P{player} mean return: {mean:+.4f} (std {std:.4f})")


def _play_human_game(
    game: LeducGame,
    rng: np.random.Generator,
    human_seat: int,
) -> None:
    ai_seat = 1 - human_seat
    human = HumanAgent(player_id=human_seat)
    ai = AnnouncingAgent(RandomAgent(rng), player_id=ai_seat)
    agents: list[Agent] = [human, ai] if human_seat == 0 else [ai, human]
    print("=== Leduc Hold'em (2p) — Human vs Random AI ===")
    print(f"You are P{human_seat}. Opponent is P{ai_seat}.")
    result = run_hand(game, agents, rng)
    print()
    print(format_hand(result))
    print()
    _print_returns(result.returns)


def _print_returns(returns: list[float]) -> None:
    parts = (f"P{player}={value:+.1f}" for player, value in enumerate(returns))
    print(f"Returns: {', '.join(parts)}")


if __name__ == "__main__":
    main(sys.argv[1:])
