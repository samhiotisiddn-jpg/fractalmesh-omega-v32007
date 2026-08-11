from __future__ import annotations


class RewardModel:
    def __init__(self, alpha: float = 0.2) -> None:
        self.alpha = alpha
        self._emas: dict[str, float] = {}
        self._best_reward = float("-inf")
        self._cumulative_regret = 0.0

    def update(self, signal: str, value: float) -> None:
        baseline = self._emas.get(signal)
        if baseline is None:
            self._emas[signal] = value
        else:
            self._emas[signal] = (self.alpha * value) + ((1 - self.alpha) * baseline)
        self._best_reward = max(self._best_reward, value)
        self._cumulative_regret += max(0.0, self._best_reward - value)

    def get_ema(self, signal: str) -> float:
        return self._emas.get(signal, 0.0)

    def get_regret(self) -> float:
        return self._cumulative_regret

    def shape_reward(self, raw: float, signal: str) -> float:
        return raw + (0.1 * self.get_ema(signal))
