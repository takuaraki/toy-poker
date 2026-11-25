"""Tests for play-kuhn / play-leduc CLI (human vs strategy)."""

from __future__ import annotations

from pathlib import Path

import pytest

from toy_poker.core.rng import make_rng
from toy_poker.examples import play_kuhn, play_leduc
from toy_poker.games.kuhn import KuhnGame
from toy_poker.games.leduc import LeducGame
from toy_poker.solvers.cfr import CFRSolver, save_strategy


def _write_strategy(game: KuhnGame | LeducGame, path: Path) -> None:
    solver = CFRSolver(game)
    solver.iterate()
    save_strategy(solver.average_strategy(), path)


def test_kuhn_strategy_requires_human(tmp_path: Path) -> None:
    path = tmp_path / "kuhn.json"
    _write_strategy(KuhnGame(), path)
    with pytest.raises(SystemExit):
        play_kuhn.main(["--strategy", str(path)])


def test_leduc_strategy_requires_human(tmp_path: Path) -> None:
    path = tmp_path / "leduc.json"
    _write_strategy(LeducGame(), path)
    with pytest.raises(SystemExit):
        play_leduc.main(["--strategy", str(path)])


def test_kuhn_human_vs_strategy_completes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "kuhn.json"
    _write_strategy(KuhnGame(), path)
    outputs: list[str] = []

    play_kuhn._play_human_game(
        KuhnGame(),
        make_rng(0),
        human_seat=0,
        strategy_path=path,
        mode="argmax",
        input_fn=lambda _prompt: "1",
        output_fn=outputs.append,
    )

    captured = capsys.readouterr()
    assert "Human vs Strategy AI" in captured.out
    assert "Returns:" in captured.out


def test_leduc_human_vs_strategy_completes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "leduc.json"
    _write_strategy(LeducGame(), path)

    play_leduc._play_human_game(
        LeducGame(),
        make_rng(0),
        human_seat=0,
        strategy_path=path,
        mode="sample",
        input_fn=lambda _prompt: "1",
        output_fn=lambda _line: None,
    )

    captured = capsys.readouterr()
    assert "Human vs Strategy AI" in captured.out
    assert "Returns:" in captured.out


def test_kuhn_human_without_strategy_still_uses_random(
    capsys: pytest.CaptureFixture[str],
) -> None:
    play_kuhn._play_human_game(
        KuhnGame(),
        make_rng(0),
        human_seat=0,
        strategy_path=None,
        input_fn=lambda _prompt: "1",
        output_fn=lambda _line: None,
    )
    captured = capsys.readouterr()
    assert "Human vs Random AI" in captured.out
