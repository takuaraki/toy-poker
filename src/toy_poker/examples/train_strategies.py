"""Train CFR average strategies and write JSON for CLI play."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
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
    started_at = datetime.now().astimezone()
    print(f"[{name}] training {iterations} iterations → {output}")
    t0 = time.perf_counter()
    for i in range(1, iterations + 1):
        solver.iterate()
        if i == iterations or i % 10 == 0:
            elapsed = time.perf_counter() - t0
            remaining = elapsed * (iterations - i) / i
            print(
                f"[{name}] {i}/{iterations} "
                f"(elapsed {elapsed:.1f}s, eta {remaining:.1f}s)"
            )
    strategy = solver.average_strategy()
    save_strategy(strategy, output)
    size_kib = output.stat().st_size / 1024
    print(f"[{name}] wrote {output} ({size_kib:.1f} KiB)")

    if report_exploitability:
        print(f"[{name}] computing exploitability…")
        expl_value = exploitability(game, strategy)
        expl_text = f"{expl_value:.6f}"
        print(f"[{name}] exploitability = {expl_text}")
    else:
        expl_text = "skip"

    finished_at = datetime.now().astimezone()
    duration_s = time.perf_counter() - t0
    log_path = output.with_suffix(".log")
    _write_train_log(
        log_path,
        started_at=started_at,
        finished_at=finished_at,
        duration_s=duration_s,
        game=name,
        iterations=iterations,
        exploitability=expl_text,
    )
    print(f"[{name}] wrote {log_path}")


def _write_train_log(
    path: Path,
    *,
    started_at: datetime,
    finished_at: datetime,
    duration_s: float,
    game: str,
    iterations: int,
    exploitability: str,
) -> None:
    path.write_text(
        "\n".join(
            [
                f"started_at: {started_at.isoformat(timespec='seconds')}",
                f"finished_at: {finished_at.isoformat(timespec='seconds')}",
                f"duration_s: {duration_s:.3f}",
                f"game: {game}",
                f"iterations: {iterations}",
                f"exploitability: {exploitability}",
                "",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(sys.argv[1:])
