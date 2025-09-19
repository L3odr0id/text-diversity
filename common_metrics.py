import numpy as np
from texts_diversity import Distances

def calc_mean_metric(distances: Distances) -> float:
    values = distances.get_values()
    return float(np.array(values).mean())


def calc_median_metric(distances: Distances) -> float:
    values = distances.get_values()
    return float(np.median(values))
