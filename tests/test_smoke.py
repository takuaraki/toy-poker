"""Smoke tests for project skeleton."""

from __future__ import annotations

import toy_poker
from toy_poker.core import make_rng
from toy_poker.core.protocols import Agent, Game, State


def test_package_version() -> None:
    assert toy_poker.__version__ == "0.1.0"


def test_make_rng_reproducible() -> None:
    rng_a = make_rng(42)
    rng_b = make_rng(42)
    assert rng_a.integers(1000) == rng_b.integers(1000)


def test_protocols_are_runtime_checkable() -> None:
    assert isinstance(Game, type)
    assert isinstance(State, type)
    assert isinstance(Agent, type)
