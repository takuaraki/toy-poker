"""Kuhn Poker CLI demo."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Literal, cast

import numpy as np

from toy_poker.agents.human import AnnouncingAgent, HumanAgent
from toy_poker.agents.random import RandomAgent
from toy_poker.agents.strategy import StrategyAgent
from toy_poker.core.protocols import Agent, Game
from toy_poker.core.rng import make_rng
from toy_poker.games.kuhn import KuhnGame
from toy_poker.runner.format import format_hand
from toy_poker.runner.hand import run_hand, run_match
from toy_poker.solvers.cfr import load_strategy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Play Kuhn Poker (2-player)")
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
        help="play one hand against an AI",
    )
    parser.add_argument(
        "--seat",
        type=int,
        default=0,
        choices=[0, 1],
        help="seat when using --human (default: 0)",
    )
    parser.add_argument(
        "--strategy",
        type=Path,
        default=None,
        help="strategy JSON for the AI opponent (requires --human)",
    )
    parser.add_argument(
        "--mode",
        choices=["sample", "argmax"],
        default="sample",
        help="StrategyAgent action selection mode (default: sample)",
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
    if args.strategy is not None and not args.human:
        parser.error("--strategy requires --human")

    game = KuhnGame()
    rng = make_rng(args.seed)

    if args.human:
        _play_human_game(
            game,
            rng,
            human_seat=args.seat,
            strategy_path=args.strategy,
            mode=args.mode,
        )
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
    game: Game,
    rng: np.random.Generator,
    human_seat: int,
    strategy_path: Path | None = None,
    mode: str = "sample",
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> None:
    ai_seat = 1 - human_seat
    human = HumanAgent(
        player_id=human_seat,
        input_fn=input_fn,
        output_fn=output_fn,
    )
    ai_inner = _build_ai_agent(rng, strategy_path=strategy_path, mode=mode)
    ai = AnnouncingAgent(ai_inner, player_id=ai_seat, output_fn=output_fn)
    agents: list[Agent] = [human, ai] if human_seat == 0 else [ai, human]

    opponent = "Strategy AI" if strategy_path is not None else "Random AI"
    print(f"=== Kuhn Poker (2p) — Human vs {opponent} ===")
    print(f"You are P{human_seat}. Opponent is P{ai_seat}.")
    if strategy_path is not None:
        print(f"Strategy: {strategy_path} (mode={mode})")
    result = run_hand(game, agents, rng)
    print()
    print(format_hand(result))
    print()
    _print_returns(result.returns)


def _build_ai_agent(
    rng: np.random.Generator,
    *,
    strategy_path: Path | None,
    mode: str,
) -> Agent:
    if strategy_path is None:
        return RandomAgent(rng)
    strategy = load_strategy(strategy_path)
    return StrategyAgent(
        strategy=strategy,
        rng=rng,
        mode=cast(Literal["sample", "argmax"], mode),
    )


def _print_returns(returns: list[float]) -> None:
    parts = (f"P{player}={value:+.1f}" for player, value in enumerate(returns))
    print(f"Returns: {', '.join(parts)}")


if __name__ == "__main__":
    main(sys.argv[1:])
