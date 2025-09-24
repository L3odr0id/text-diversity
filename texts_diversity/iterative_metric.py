from typing import List
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IterativeMetricCalculationResult:
    value: float
    texts: List[str]
    finished: bool


class IterativeMetric(ABC):
    """Base class for iterative metrics that can manipulate texts set"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calc(self, texts: List[str]) -> IterativeMetricCalculationResult:
        """
        Calculate the metric value for the given texts.
        """
        pass
