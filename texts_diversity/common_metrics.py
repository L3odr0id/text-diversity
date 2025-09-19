import numpy as np

from texts_diversity.texts_distances import TextsDistances


def calc_mean_metric(distances: TextsDistances) -> float:
    values = distances.get_normalized_values()
    return float(np.array(values).mean())


def calc_median_metric(distances: TextsDistances) -> float:
    values = distances.get_normalized_values()
    return float(np.median(values))
