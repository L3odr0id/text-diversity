from dataclasses import dataclass
from typing import Callable

from texts_diversity.texts_distances import TextsDistances
from texts_diversity.metric import Metric
from texts_diversity.algo import Algo


class CalcInfo:
    def __init__(self, metric: Metric, algo: Algo):
        self.metric = metric
        self.distances = TextsDistances(algo=algo)

    def label(self) -> str:
        return f"{self.metric.name} ({self.distances.algo.name})"

    def value(self, distances: TextsDistances) -> float:
        return self.metric.calc(distances)
