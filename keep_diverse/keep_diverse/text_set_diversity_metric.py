from abc import ABC, abstractmethod
from .text_set_distances_list import (
    TextSetDistancesList,
)


class TextSetDiversityMetric(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def value(self, text_set_distances: TextSetDistancesList) -> float:
        pass
