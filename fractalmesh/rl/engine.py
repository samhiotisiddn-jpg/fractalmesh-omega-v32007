from __future__ import annotations

import math
import random


class RLEngine:
    def __init__(self, actions: list[str], exploration_rate: float = 0.1) -> None:
        if not actions:
            raise ValueError("actions must not be empty")
        self.actions = actions
        self.exploration_rate = exploration_rate
        self.action_counts = {action: 0 for action in actions}
        self.action_values = {action: 0.0 for action in actions}

    def _softmax_action(self) -> str:
        values = [self.action_values[action] for action in self.actions]
        max_value = max(values)
        weights = [math.exp(value - max_value) for value in values]
        total_weight = sum(weights) or 1.0
        probabilities = [weight / total_weight for weight in weights]
        return random.choices(self.actions, weights=probabilities, k=1)[0]

    def select_action(self, state: dict) -> str:
        del state
        unseen = [action for action, count in self.action_counts.items() if count == 0]
        if unseen:
            return random.choice(unseen)
        if random.random() < self.exploration_rate:
            return self._softmax_action()
        total = sum(self.action_counts.values()) + 1
        best_action = self.actions[0]
        best_score = float("-inf")
        for action in self.actions:
            count = max(self.action_counts[action], 1)
            bonus = math.sqrt((2.0 * math.log(total)) / count)
            score = self.action_values[action] + bonus
            if score > best_score:
                best_score = score
                best_action = action
        return best_action

    def update(self, action: str, reward: float) -> None:
        if action not in self.action_counts:
            raise KeyError(f"unknown action: {action}")
        count = self.action_counts[action] + 1
        previous = self.action_values[action]
        self.action_counts[action] = count
        self.action_values[action] = previous + (reward - previous) / count
