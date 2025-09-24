from typing import List, Dict, Tuple, Optional, Callable

from texts_diversity.algo import Algo


class TextsDistances:
    def __init__(
        self,
        algo: Algo,
        normalize: Optional[Callable[[List[float]], List[float]]] = None,
    ):
        self.algo = algo
        self.data: Dict[Tuple[int, int], Optional[float]] = {}
        self.normalize = normalize

    def add_dist(self, old_texts: List[str], new_text: str):
        current_idx = len(old_texts)

        # Calculate distances with all previous texts
        for prev_idx, prev_text in enumerate(old_texts):
            try:
                distance_value = self.algo.func(new_text, prev_text)
            except Exception as e:
                print(
                    f"Error calculating distance for pair ({prev_idx}, {current_idx}): {e}"
                )
                distance_value = float("nan")

            self.data[(prev_idx, current_idx)] = distance_value

    def max_key(self) -> int:
        return max(max(i, j) for i, j in self.data.keys())

    def distance(self, from_idx: int, to_idx: int) -> float:
        """Get distance between two texts by their indices."""
        if (from_idx, to_idx) in self.data and self.data[
            (from_idx, to_idx)
        ] is not None:
            return self.data[(from_idx, to_idx)]
        elif (to_idx, from_idx) in self.data and self.data[
            (to_idx, from_idx)
        ] is not None:
            return self.data[(to_idx, from_idx)]
        else:
            raise ValueError(f"Distance ({from_idx}, {to_idx}) is not in storage")

    def find_minimax_center(self) -> Tuple[int, float, Dict[int, float]]:
        """Find the most centered text using minimax method."""
        num_texts = self.max_key() + 1
        max_distances = {}

        # Calculate max distance for all texts
        for i in range(num_texts):
            max_dist = 0.0
            for j in range(num_texts):
                if i != j:
                    try:
                        dist = self.distance(i, j)
                        max_dist = max(max_dist, dist)
                    except ValueError:
                        continue

            max_distances[i] = max_dist

        # Find the index with minimum maximum distance
        center_idx = min(max_distances.keys(), key=lambda k: max_distances[k])
        min_max_distance = max_distances[center_idx]

        return center_idx, min_max_distance, max_distances

    def get_normalized_values(self) -> List[float]:
        values = list(self.data.values())
        if self.normalize:
            return self.normalize(values)
        return values
