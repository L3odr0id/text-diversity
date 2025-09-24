import time
import random
from typing import List, Union
import matplotlib.pyplot as plt

from texts_diversity.plot import Plot
from texts_diversity.utils import save_plot_safely

from texts_diversity.iterative_metric import (
    IterativeMetric,
    IterativeMetricCalculationResult,
)
from texts_diversity.metric import Metric
from texts_diversity.texts_distances import TextsDistances
from texts_diversity.algo import Algo


class RemovePercentageMetric(IterativeMetric):
    def __init__(
        self, metric: Metric, algo: Algo, eps: float, max_tries: int, output_file: str
    ):
        super().__init__("Remove Percentage Metric")
        self.metric = metric
        self.algo = algo
        self.eps = eps
        self.max_tries = max_tries
        self.output_file = output_file

    def metric_value_for_texts(self, texts: List[str]) -> float:
        distances = TextsDistances(self.algo)
        for i, text in enumerate(texts):
            distances.add_dist(texts[:i], text)
        return self.metric.calc(distances)

    def try_to_remove_texts(
        self,
        texts: List[str],
        removal_percentage: float,
        current_value: float,
        iteration: int,
    ) -> Union[List[str], bool, float]:
        texts_count = len(texts)
        num_to_remove = int(texts_count * removal_percentage)
        if texts_count < 2 or num_to_remove < 1:
            return texts, True, current_value

        for attempt in range(self.max_tries):
            texts_to_remove = random.sample(texts, num_to_remove)
            remaining_texts = [text for text in texts if text not in texts_to_remove]
            new_value = self.metric_value_for_texts(remaining_texts)
            metric_change = abs(new_value - current_value)
            print(
                f"[attempt] Iter {iteration}. Try {attempt + 1}. Remove {removal_percentage}% ({num_to_remove}). Old {current_value}. New {new_value}. Diff: {metric_change}. eps: {self.eps}."
            )
            if metric_change <= self.eps:
                print(
                    f"[attempt] Iter {iteration}. Try {attempt + 1}. Successfully removed texts. Removed {removal_percentage}% ({num_to_remove})"
                )
                return remaining_texts, False, new_value
        print(
            f"[attempt] Iter {iteration}. Try {attempt + 1}. Failed to remove texts. Tried to remove {removal_percentage}% ({num_to_remove})"
        )
        return texts, False, current_value

    def search_for_removal_percentage(
        self, texts: List[str], initial_value: float, iteration: int
    ) -> Union[List[str], float]:
        print(
            f"[search] Start searching for removal percentage. Iter {iteration}. Initial value: {initial_value}. Texts count: {len(texts)}."
        )
        left = 0
        right = 100

        res_texts = texts
        res_value = initial_value

        while left <= right:
            mid = (left + right) // 2
            print(
                f"[search] Iter {iteration}. Mid: {mid}. Left: {left}. Right: {right}. Init texts count: {len(texts)}. Possible result count {len(res_texts)}."
            )

            new_texts, isFinished, new_value = self.try_to_remove_texts(
                texts,
                mid / 100,
                initial_value,
                iteration,
            )

            if isFinished:
                num_to_remove = int(len(texts) * mid / 100)
                print(
                    f"[search] Iter {iteration}. Tried to remove {mid / 100}% ({num_to_remove}). Break."
                )
                return (texts, initial_value)

            removed_successfully = len(new_texts) < len(texts)

            if removed_successfully:
                res_texts = new_texts
                res_value = new_value
                print(
                    f"[search] Iter {iteration}. Removed {mid / 100}%. New value: {new_value}. New texts count: {len(new_texts)}."
                )
                left = mid + 1
            else:
                print(f"[search] Iter {iteration}. Did not removed {mid / 100}%.")
                right = mid - 1

        print(
            f"[search] Iter {iteration}. Finished. Removed {mid / 100}%. New value: {res_value}. New texts count: {len(res_texts)}."
        )
        return (res_texts, res_value)

    def calc(self, texts: List[str]):
        metric_value = self.metric_value_for_texts(texts)
        successfuly_shrinked = True
        iteration = 1
        while successfuly_shrinked and len(texts) > 2:
            new_texts, new_value = self.search_for_removal_percentage(
                texts, metric_value, iteration=iteration
            )
            successfuly_shrinked = len(new_texts) < len(texts)
            texts = new_texts
            metric_value = new_value
            iteration += 1

        # Draw graphs

    # def draw(self, y_values: List[float], x_values: List[int]):
    #     fig, ax = plt.subplots(1, 1, figsize=(10, 6))
    #     series = {"Number of texts": y_values}
    #     plot = Plot(
    #         ax=ax,
    #         x_values=x_values,
    #         x_name="Iteration",
    #         series=series,
    #         y_name="Number of texts",
    #         title="Remove Percentage with metric "
    #         + self.metric.name
    #         + " and algo "
    #         + self.algo.name,
    #     )
    #     plot.draw()

    #     save_plot_safely(fig, self.output_file)
