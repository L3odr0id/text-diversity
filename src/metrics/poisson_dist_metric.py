from scipy.stats import poisson

from texts_diversity.metric import Metric
from texts_diversity.texts_distances import TextsDistances


def calc_poisson_distribution(distances: TextsDistances) -> float:
    distance_values = distances.get_normalized_values()
    distance_values.sort()
    values = []
    for i in range(len(distance_values)):
        value = 2 * distance_values[i] * poisson.pmf(i, len(distance_values))
        values.append(value)
    return sum(values)


class PoissonDistMetric(Metric):
    def __init__(self):
        super().__init__("Poisson_dist", calc_poisson_distribution)


def poisson_dist_metric():
    return PoissonDistMetric()
