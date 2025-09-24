from texts_diversity.texts_distances import TextsDistances


def min_distance_from_last(distances: TextsDistances) -> float:
    try:
        last_idx = distances.max_key()
    except ValueError:
        return 0.0

    if last_idx == 0:
        return 0.0  # Only one text available

    distances_list = [distances.distance(last_idx, i) for i in range(last_idx)]
    if not distances_list:
        return 0.0
    return min(distances_list)


class MinDistanceMetric:
    def __init__(self):
        self.sum_of_min_distances = 0.0
        print(f"MinDistanceMetric initialized")

    def calc(self, distances: TextsDistances) -> float:
        min_d = min_distance_from_last(distances)
        self.sum_of_min_distances += min_d
        return self.sum_of_min_distances
