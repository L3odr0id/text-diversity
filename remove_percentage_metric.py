import time
import random
from dataclasses import dataclass
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
from texts_diversity.calc_info import CalcInfo


@dataclass
class PercentageFilterPlotInfo:
    iterations: int
    texts_count_per_iter: List[int]
    metric_values_per_iter: List[float]
    metric_name: str
    algo_name: str


class RemovePercentageMetric:
    def __init__(
        self,
        calc_info: CalcInfo,
        eps: float,
        max_tries: int,
        initial_texts: List[str],
    ):
        self.metric = calc_info.metric
        self.algo = calc_info.distances.algo
        self.eps = eps
        self.max_tries = max_tries
        self.original_texts = initial_texts
        self.current_indices = list(range(len(initial_texts)))
        self.iteration = 0
        self.texts_count_per_iter = [len(initial_texts)]
        self.metric_values_per_iter = []
        self.is_finished = False
        self.all_distances = calc_info.distances
        self.metric_value = self.metric.calc(self.all_distances)
        self.original_texts_indices_set = set(range(len(initial_texts)))

        self.metric_values_per_iter = [self.metric_value]

    @property
    def filtered_texts(self) -> List[str]:
        return [self.original_texts[i] for i in self.current_indices]

    def metric_value_for_remaining_texts(
        self, remaining_text_indices: List[int]
    ) -> float:
        distances_copy = self.all_distances.copy()

        texts_to_remove = self.original_texts_indices_set - set(remaining_text_indices)
        print(
            f"texts_to_remove: {len(texts_to_remove)}. distances_len_before: {len(distances_copy.data)}"
        )
        distances_copy.remove_list(list(texts_to_remove))
        print(
            f"texts_to_remove: {len(texts_to_remove)}. distances_len_after: {len(distances_copy.data)}"
        )

        return self.metric.calc(distances_copy)

    def basic_info_log(self) -> str:
        return f"Metric: {self.metric.name}. Algo: {self.algo.name}. Iter: {self.iteration}."

    def try_to_remove_texts(
        self,
        text_indices: List[int],
        removal_percentage: float,
        current_value: float,
    ) -> Union[List[int], bool, float]:
        texts_count = len(text_indices)
        num_to_remove = int(texts_count * removal_percentage)
        if texts_count <= 2 or num_to_remove < 1 or removal_percentage == 1.0:
            return text_indices, True, current_value

        for attempt in range(self.max_tries):
            indices_to_remove = random.sample(text_indices, num_to_remove)
            remaining_indices = [
                idx for idx in text_indices if idx not in indices_to_remove
            ]

            # We want to avoid removing too many texts and left at least 10 texts
            if len(remaining_indices) <= 10:
                print(
                    f"[attempt] {self.basic_info_log()} Try {attempt + 1}. Too few texts left, so fail this attempt. Tried to remove {removal_percentage * 100}% ({num_to_remove}). Left {len(remaining_indices)} texts."
                )
                return text_indices, False, current_value

            start_time = time.time()
            new_value = self.metric_value_for_remaining_texts(remaining_indices)
            elapsed_time = time.time() - start_time
            # print(
            #     f"[attempt] {self.basic_info_log()} Metric value calculation took {elapsed_time:.4f} seconds."
            # )

            metric_change = current_value - new_value
            eps_change = self.eps * current_value
            print(
                f"[attempt] {self.basic_info_log()} Try {attempt + 1}. Remove {removal_percentage * 100}% ({num_to_remove}). Old {current_value}. New {new_value}. Diff: {metric_change}. eps: {self.eps}. eps*prev_value: {eps_change}."
            )
            if metric_change <= eps_change:
                print(
                    f"[attempt] {self.basic_info_log()} Try {attempt + 1}. Successfully removed texts. Removed {removal_percentage * 100}% ({num_to_remove})"
                )
                return remaining_indices, False, new_value
        print(
            f"[attempt] {self.basic_info_log()} Try {attempt + 1}. Failed to remove texts. Tried to remove {removal_percentage * 100}% ({num_to_remove})"
        )
        return text_indices, False, current_value

    def search_for_removal_percentage(
        self, text_indices: List[int], initial_value: float
    ) -> Union[List[int], float]:
        print(
            f"[search] Start searching for removal percentage. {self.basic_info_log()} Initial value: {initial_value}. Texts count: {len(text_indices)}."
        )
        left = 0
        right = 100

        res_indices = text_indices
        res_value = initial_value
        successfuly_removed_percentage = 0.0

        while left <= right:
            mid = (left + right) // 2
            print(
                f"[search] {self.basic_info_log()} Mid: {mid}. Left: {left}. Right: {right}. Init texts count: {len(text_indices)}. Possible result count {len(res_indices)}."
            )

            new_indices, isFinished, new_value = self.try_to_remove_texts(
                text_indices,
                mid / 100,
                initial_value,
            )

            if isFinished:
                num_to_remove = int(len(text_indices) * mid / 100)
                print(
                    f"[search] {self.basic_info_log()} Tried to remove {mid / 100}% ({num_to_remove}). Break."
                )
                return (text_indices, initial_value)

            removed_successfully = len(new_indices) < len(text_indices)

            if removed_successfully:
                res_indices = new_indices
                res_value = new_value
                successfuly_removed_percentage = mid / 100
                print(
                    f"[search] {self.basic_info_log()} Removed {mid / 100}%. New value: {new_value}. New texts count: {len(new_indices)}."
                )
                left = mid + 1
            else:
                print(f"[search] {self.basic_info_log()} Did not removed {mid / 100}%.")
                right = mid - 1

        print(
            f"[search] {self.basic_info_log()} Finished. Removed {successfuly_removed_percentage}%. New value: {res_value}. New texts count: {len(res_indices)}."
        )
        return (res_indices, res_value)

    def iterate(self):
        if self.is_finished:
            return

        new_indices, new_value = self.search_for_removal_percentage(
            self.current_indices, self.metric_value
        )
        successfuly_shrinked = len(new_indices) < len(self.current_indices)

        self.current_indices = new_indices
        self.metric_value = new_value
        self.is_finished = (not successfuly_shrinked) or len(self.current_indices) <= 2
        if not self.is_finished:
            self.iteration += 1
            self.texts_count_per_iter.append(len(self.current_indices))
            self.metric_values_per_iter.append(self.metric_value)

    def plot_info(self) -> PercentageFilterPlotInfo:
        return PercentageFilterPlotInfo(
            iterations=self.iteration,
            texts_count_per_iter=self.texts_count_per_iter,
            metric_values_per_iter=self.metric_values_per_iter,
            metric_name=self.metric.name,
            algo_name=self.algo.name,
        )
