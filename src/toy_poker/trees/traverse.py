"""Game tree traversal and information-set collection."""
from __future__ import annotations

from collections.abc import Iterator

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action


def traverse_game_tree(game: Game) -> Iterator[State]:
    raise NotImplementedError


def collect_infosets(game: Game) -> dict[str, list[Action]]:
    raise NotImplementedError