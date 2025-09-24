from typing import List, Callable

from texts_diversity.algo import Algo
from texts_diversity.texts_distances import TextsDistances
from texts_diversity.calc_info import CalcInfo
from texts_diversity.metric import Metric


def cis_same_metric(algos: List[Algo], metric: Callable[[], Metric]) -> list[CalcInfo]:
    return [CalcInfo(metric=metric(), algo=algo) for algo in algos]
