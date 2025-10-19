from dataclasses import dataclass
from typing import Callable, List

from texts_diversity.texts_distances import TextsDistances
from texts_diversity.metric import Metric
from texts_diversity.algo import Algo


class CalcInfo:
    def __init__(self, metric: Metric, algo: Algo):
        self.metric = metric
        self.distances = TextsDistances(algo=algo)

    def label(self) -> str:
        return f"{self.metric.name} ({self.distances.algo.name})"

    def current_value(self) -> float:
        return self.metric.calc(self.distances)

    def value(self, distances: TextsDistances) -> float:  # TODO: remove. Deprecated.
        return self.metric.calc(distances)

    def value_without_idxs(self, idxs_to_remove: List[int]) -> float:
        distances_copy = self.distances.copy()
        distances_copy.remove_list(idxs_to_remove)
        return self.metric.calc(distances_copy)
