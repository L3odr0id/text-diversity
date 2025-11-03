from typing import List

from .text_set_distances_list import (
    TextSetDistancesList,
)
from .text_set_diversity_metric import (
    TextSetDiversityMetric,
)


def metric_value_without_idxs(
    text_set_distances: TextSetDistancesList,
    metric: TextSetDiversityMetric,
    idxs_to_remove: List[int],
) -> float:
    new_text_set_distances = text_set_distances.copy()
    new_text_set_distances.remove_list(idxs_to_remove)
    return metric.value(new_text_set_distances)
