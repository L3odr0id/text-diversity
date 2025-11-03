from scipy.stats import poisson

from .text_set_distances_list import (
    TextSetDistancesList,
)
from .text_set_diversity_metric import (
    TextSetDiversityMetric,
)


class PoissonMetric(TextSetDiversityMetric):

    def __init__(self):
        super().__init__("Poisson_dist")

    def value(self, text_set_distances: TextSetDistancesList) -> float:
        distance_values = text_set_distances.values()
        distance_values.sort()
        values = []
        for i in range(len(distance_values)):
            value = 2 * distance_values[i] * poisson.pmf(i, len(distance_values))
            values.append(value)
        return sum(values)
