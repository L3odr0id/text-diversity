from typing import List

from texts_diversity.metric import Metric
from texts_diversity.algo import Algo
from texts_diversity.texts_distances import TextsDistances


class PlotConfig:
    def __init__(self, name: str, metric: Metric, algos: List[Algo]):
        self.name = name
        self.metric = metric
        self.texts_distances = [TextsDistances(algo=algo) for algo in algos]
