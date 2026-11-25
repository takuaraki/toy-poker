"""Train CFR average strategies and write JSON for CLI play."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from toy_poker.core.protocols import Game
from toy_poker.games.kuhn import KuhnGame
from toy_poker.games.leduc import LeducGame
from toy_poker.solvers.cfr import CFRSolver, save_strategy
from toy_poker.solvers.evaluate import exploitability

DEFAULT_ITERATIONS: dict[str, int] = {
    "kuhn": 5_000,
    "leduc": 1_000,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Train CFR strategies and save JSON for play-kuhn / play-leduc",
    )
    parser.add_argument(
        "--game",
        choices=["kuhn", "leduc", "all"],
        default="all",
        help="which game(s) to train (default: all)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="CFR iterations (default: kuhn=5000, leduc=1000)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("strategies"),
        help="directory for strategy JSON (default: strategies/)",
    )
    parser.add_argument(
        "--skip-exploitability",
        action="store_true",
        help="skip exploitability report (faster for Leduc)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.iterations is not None and args.iterations < 1:
        parser.error("--iterations must be at least 1")

    games = ["kuhn", "leduc"] if args.game == "all" else [args.game]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    for name in games:
        iterations = (
            args.iterations if args.iterations is not None else DEFAULT_ITERATIONS[name]
        )
        output = args.output_dir / f"{name}.json"
        _train_one(
            name,
            iterations=iterations,
            output=output,
            report_exploitability=not args.skip_exploitability,
        )


def _make_game(name: str) -> Game:
    if name == "kuhn":
        return KuhnGame()
    if name == "leduc":
        return LeducGame()
    raise ValueError(f"unknown game: {name}")


def _train_one(
    name: str,
    *,
    iterations: int,
    output: Path,
    report_exploitability: bool,
) -> None:
    game = _make_game(name)
    solver = CFRSolver(game)
    print(f"[{name}] training {iterations} iterations → {output}")
    t0 = time.perf_counter()
    for i in range(1, iterations + 1):
        solver.iterate()
        if i == iterations or i % max(1, iterations // 10) == 0:
            elapsed = time.perf_counter() - t0
            print(f"[{name}] {i}/{iterations} ({elapsed:.1f}s)")
    strategy = solver.average_strategy()
    save_strategy(strategy, output)
    size_kib = output.stat().st_size / 1024
    print(f"[{name}] wrote {output} ({size_kib:.1f} KiB)")

    if report_exploitability:
        print(f"[{name}] computing exploitability…")
        expl = exploitability(game, strategy)
        print(f"[{name}] exploitability = {expl:.6f}")


if __name__ == "__main__":
    main(sys.argv[1:])
