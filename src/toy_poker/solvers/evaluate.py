"""Evaluate strategies."""

from __future__ import annotations

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action, PlayerId, Strategy
from toy_poker.trees.traverse import collect_infosets


def expected_returns(game: Game, strategy: Strategy) -> list[float]:
    """Expected payoffs when both players follow ``strategy``."""

    def walk(state: State) -> list[float]:
        if state.is_terminal():
            return list(state.returns())

        if state.is_chance_node():
            values = [0.0, 0.0]
            for action, prob in state.chance_outcomes():
                child_values = walk(state.apply_action(action))
                values[0] += child_values[0] * prob
                values[1] += child_values[1] * prob
            return values

        player = state.current_player()
        key = state.information_state_string(player)
        probs = strategy[key]
        values = [0.0, 0.0]
        for action in state.legal_actions():
            child_values = walk(state.apply_action(action))
            values[0] += child_values[0] * probs[action]
            values[1] += child_values[1] * probs[action]
        return values

    return walk(game.new_initial_state())


def _compute_best_response_strategy(
    game: Game,
    strategy: Strategy,
    player: PlayerId,
    *,
    max_iters: int = 100,
) -> Strategy:
    """
    Best response strategy for ``player`` when the other player follows ``strategy``.

    Uses iterative counterfactual best response: action values are computed with
    continuation play according to the current BR (not history-wise max), then the
    BR is updated to a pure argmax at each infoset until stable.
    """
    infosets = collect_infosets(game)
    # 初期 BR は一様。反復で player の infoset だけ純戦略に寄っていく
    br: Strategy = {
        key: {action: 1.0 / len(actions) for action in actions}
        for key, actions in infosets.items()
    }

    action_cf: dict[str, dict[Action, float]] = {}
    for _ in range(max_iters):
        action_cf.clear()

        def walk(
            state: State, reach_p0: float, reach_p1: float, reach_chance: float
        ) -> float:
            if state.is_terminal():
                return state.returns()[player]

            if state.is_chance_node():
                return sum(
                    prob
                    * walk(
                        state.apply_action(action),
                        reach_p0,
                        reach_p1,
                        reach_chance * prob,
                    )
                    for action, prob in state.chance_outcomes()
                )

            acting_player = state.current_player()
            actions = state.legal_actions()
            key = state.information_state_string(acting_player)

            if acting_player == player:
                weight = (reach_p1 if player == 0 else reach_p0) * reach_chance
                bucket = action_cf.setdefault(key, {a: 0.0 for a in actions})
                action_values: dict[Action, float] = {}
                for action in actions:
                    # 全行動を探索（深い infoset の CF も埋める）。
                    # 子以降の BR 手番は現在の br に従って価値が返る。
                    child_value = walk(
                        state.apply_action(action),
                        reach_p0,
                        reach_p1,
                        reach_chance,
                    )
                    action_values[action] = child_value
                    bucket[action] += weight * child_value
                probs = br[key]
                return sum(probs[action] * action_values[action] for action in actions)

            probs = strategy[key]
            total_value = 0.0
            for action in actions:
                prob = probs[action]
                if acting_player == 0:
                    child_value = walk(
                        state.apply_action(action),
                        reach_p0 * prob,
                        reach_p1,
                        reach_chance,
                    )
                else:
                    child_value = walk(
                        state.apply_action(action),
                        reach_p0,
                        reach_p1 * prob,
                        reach_chance,
                    )
                total_value += child_value * prob
            return total_value

        walk(game.new_initial_state(), 1.0, 1.0, 1.0)

        changed = False
        for key, values in action_cf.items():
            best_action = max(values, key=lambda action: values[action])
            new_policy = {a: (1.0 if a == best_action else 0.0) for a in values}
            if new_policy != br[key]:
                changed = True
            br[key] = new_policy

        if not changed:
            break

    return {key: br[key] for key in action_cf}


def best_response_value(game: Game, strategy: Strategy, player: PlayerId) -> float:
    """Best response value for ``player`` when the other player follows ``strategy``."""
    best_response_strategy = _compute_best_response_strategy(game, strategy, player)
    profile = {
        **strategy,
        **best_response_strategy,
    }  # 同じInfosetはbest responseで上書き
    return expected_returns(game, profile)[player]


def nash_conv(game: Game, strategy: Strategy) -> float:
    """Nash conv of ``strategy``."""
    values = expected_returns(game, strategy)
    return sum(
        best_response_value(game, strategy, player) - values[player]
        for player in range(game.num_players())
    )


def exploitability(game: Game, strategy: Strategy) -> float:
    """Exploitability of ``strategy`` (NashConv / num_players)."""
    return nash_conv(game, strategy) / game.num_players()
