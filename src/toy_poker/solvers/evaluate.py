"""Evaluate strategies."""

from __future__ import annotations

from toy_poker.core.protocols import Game, State
from toy_poker.core.types import Action, PlayerId, Strategy


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
    game: Game, strategy: Strategy, player: PlayerId
) -> Strategy:
    """
    Best response strategy for ``player`` when the other player follows ``strategy``.
    """
    # infoset -> action -> 累積 counterfactual value
    action_cf: dict[str, dict[Action, float]] = {}

    def walk(
        state: State, reach_p0: float, reach_p1: float, reach_chance: float
    ) -> float:
        if state.is_terminal():
            return state.returns()[player]

        if state.is_chance_node():
            return sum(
                prob
                * walk(
                    state.apply_action(action), reach_p0, reach_p1, reach_chance * prob
                )
                for action, prob in state.chance_outcomes()
            )

        # state is player's turn
        acting_player = state.current_player()
        actions = state.legal_actions()
        key = state.information_state_string(acting_player)

        if acting_player == player:
            weight = (reach_p1 if player == 0 else reach_p0) * reach_chance
            if key not in action_cf:
                action_cf[key] = {a: 0.0 for a in actions}

            best_value = -float("inf")
            for action in actions:
                if player == 0:
                    value = walk(
                        state.apply_action(action),
                        reach_p0 * 1.0,  # この行動を必ず選ぶ
                        reach_p1,
                        reach_chance,
                    )
                else:
                    value = walk(
                        state.apply_action(action),
                        reach_p0,
                        reach_p1 * 1.0,  # この行動を必ず選ぶ
                        reach_chance,
                    )
                action_cf[key][action] += weight * value
                best_value = max(best_value, value)
            return best_value

        else:
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

    best_response_strategy: Strategy = {}
    for key, values in action_cf.items():
        best_action = max(values, key=lambda action: values[action])
        best_response_strategy[key] = {
            a: (1.0 if a == best_action else 0.0) for a in values
        }
    return best_response_strategy


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
    """Exploitability of ``strategy``."""
    return nash_conv(game, strategy) / game.num_players()
