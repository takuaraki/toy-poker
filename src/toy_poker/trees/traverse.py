from toy_poker.core.protocols import Game, State, Action
from typing import Iterator

def traverse_game_tree(game: Game) -> Iterator[State]: 
    return NotImplemented

def collect_infosets(game: Game) -> dict[str, list[Action]]: 
    return NotImplemented