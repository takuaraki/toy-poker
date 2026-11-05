"""Game tree traversal and information-set collection."""

from __future__ import annotations

from collections.abc import Iterator

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action


def traverse_game_tree(game: Game) -> Iterator[State]:
    initial_state = game.new_initial_state()
    stack: list[State] = [initial_state]
    while stack:
        state = stack.pop()

        # このstateを返す
        yield state

        # 子ノードをstackに追加
        if state.is_terminal():
            # 終端ノードの場合は子ノードがないのでスキップ
            continue
        if state.is_chance_node():
            # チャンスノードの場合は、サンプリングしうる全ての結果を子ノードとして追加
            for outcome in state.chance_outcomes():
                # 各結果に対して、stateを更新した新しいstateを子ノードとして追加
                stack.append(state.apply_action(outcome[0]))
        else:
            # プレイヤーノードの場合は、合法手を子ノードとして追加
            for action in state.legal_actions():
                # 各合法手に対して、stateを更新した新しいstateを子ノードとして追加
                stack.append(state.apply_action(action))


def collect_infosets(game: Game) -> dict[str, list[Action]]:
    infosets: dict[str, list[Action]] = {}

    for state in traverse_game_tree(game):
        # プレイヤーノードのみを対象とする
        if state.is_terminal() or state.is_chance_node():
            continue
        # 情報集合をキー、合法手を値として追加
        player = state.current_player()
        key = state.information_state_string(player)
        actions = state.legal_actions()

        existing = infosets.get(key)
        if existing is None:
            # 情報集合が存在しない場合は、合法手を追加
            infosets[key] = actions
        elif existing != actions:
            # 情報集合が存在する場合は、合法手が一致しない場合はエラー
            msg = (
                "inconsistent legal actions at infoset "
                f"{key!r}: {existing} vs {actions}"
            )
            raise ValueError(msg)

    return infosets
