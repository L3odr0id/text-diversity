from dataclasses import dataclass
from typing import Callable

from texts_diversity.texts_distances import TextsDistances


@dataclass
class Metric:
    name: str
    calc: Callable[[TextsDistances], float]
