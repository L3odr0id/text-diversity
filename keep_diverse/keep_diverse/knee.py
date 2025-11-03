from typing import List
from collections import Counter

from kneed import KneeLocator


class Knee:
    def __init__(self, counter: Counter):
        self.counter = counter
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        self.file_names, self.y_values = zip(*sorted_items)
        self.x_values = list(range(len(self.y_values)))

        kneedle = KneeLocator(
            self.x_values,
            self.y_values,
            S=1,
            curve="concave",
            direction="decreasing",
            interp_method="polynomial",
            polynomial_degree=3,
        )
        self.value = int(kneedle.knee)

    def good_files(self) -> List[str]:
        return self.file_names[self.value :]
