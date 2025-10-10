import time
import random
from dataclasses import dataclass
from typing import List, Union

from texts_diversity.texts_distances import TextsDistances
from texts_diversity.calc_info import CalcInfo
from texts_diversity.files_list import FilesList
from tests_runner import TestsRunner, TestsRunnerResult, TestsRunnerFolder

from src.basic.plot_data import PlotData


@dataclass
class PercentageFilterPlotInfo:
    iterations: int
    texts_count_per_iter: List[int]
    left_y_name: str
    main_metric_label: str
    main_metric_values: List[float]
    main_metric_color: str
    right_y_name: str
    compare_metric_label: str
    compare_metric_values: List[float]
    compare_metric_color: str


class RemovePercentageCompareFilter:
    def __init__(
        self,
        main_calc_info: CalcInfo,
        compare_calc_info: CalcInfo,
        relative_eps: float,
        max_tries: int,
        tests_runner: TestsRunner,
        files_list: FilesList,
        test_runner_folder: TestsRunnerFolder,
        report_file_path: str,
    ):
        self.total_files_count = len(files_list.file_paths)
        self.main_calc_info = main_calc_info
        self.compare_calc_info = compare_calc_info
        self.relative_eps = relative_eps
        self.max_tries = max_tries
        self.current_indices = list(range(self.total_files_count))
        self.iteration = 0
        self.is_finished = False
        self.report_file_path = report_file_path
        self.metric_value = self.main_calc_info.value(self.main_calc_info.distances)
        initial_compare_metric_value = self.compare_calc_info.value(
            self.compare_calc_info.distances
        )
        self.original_texts_indices_set = set(range(self.total_files_count))
        self.tests_runner = tests_runner
        self.files_list = files_list

        self.plot_data = PlotData(
            x_values=[],
            x_name="Not used",
            left_series={self.main_calc_info.label(): [self.metric_value]},
            left_y_name=f"Main metric value",
            right_y_name=f"Compare metric value",
            right_series={
                self.compare_calc_info.label(): [initial_compare_metric_value]
            },
            title="Metric values vs Filter iteration",
        )
        self.texts_count_per_iter = [self.total_files_count]

        self.tests_runner_folder = test_runner_folder
        self.tests_runner_folder.setup()
        self.tests_runner_folder.copy_files(self.filtered_file_paths)
        tests_runner.execute()
        self.original_errors_count = TestsRunnerResult(report_file_path).read_result()
        self.errors_count_per_iteration = [
            self.original_errors_count
        ]  # Store errors count for each iteration

    @property
    def filtered_file_paths(self) -> List[str]:
        return [self.files_list.file_paths[i] for i in self.current_indices]

    def text_distance_for_remaining_indices(
        self, text_distances: TextsDistances, remaining_text_indices: List[int]
    ) -> TextsDistances:
        text_distances_copy = text_distances.copy()
        texts_to_remove = self.original_texts_indices_set - set(remaining_text_indices)
        text_distances_copy.remove_list(list(texts_to_remove))
        return text_distances_copy

    def metric_value_for_remaining_texts(
        self, remaining_text_indices: List[int]
    ) -> float:
        distances_copy = self.text_distance_for_remaining_indices(
            self.main_calc_info.distances, remaining_text_indices
        )
        return self.main_calc_info.value(distances_copy)

    def compare_metric_value_for_remaining_texts(self) -> float:
        distances_copy = self.text_distance_for_remaining_indices(
            self.compare_calc_info.distances, self.current_indices
        )
        return self.compare_calc_info.value(distances_copy)

    def basic_info_log(self) -> str:
        return f"Metric: {self.main_calc_info.metric.name}. Algo: {self.main_calc_info.distances.algo.name}. Iter: {self.iteration}."

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
            print(
                f"[attempt] {self.basic_info_log()} Metric value calculation took {elapsed_time:.4f} seconds."
            )

            metric_change = current_value - new_value
            eps_change = self.relative_eps * current_value
            print(
                f"[attempt] {self.basic_info_log()} Try {attempt + 1}. Remove {removal_percentage * 100}% ({num_to_remove}). Old {current_value}. New {new_value}. Diff: {metric_change}. relative_eps: {self.relative_eps}. relative_eps*prev_value: {eps_change}."
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

            new_remaining_indices, isFinished, new_value = self.try_to_remove_texts(
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

            removed_successfully = len(new_remaining_indices) < len(text_indices)

            if removed_successfully:
                res_indices = new_remaining_indices
                res_value = new_value
                successfuly_removed_percentage = mid / 100
                print(
                    f"[search] {self.basic_info_log()} Removed {mid / 100}%. New value: {new_value}. New texts count: {len(new_remaining_indices)}."
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

        new_remaining_indices, new_value = self.search_for_removal_percentage(
            self.current_indices, self.metric_value
        )
        successfuly_shrinked = len(new_remaining_indices) < len(self.current_indices)

        self.current_indices = new_remaining_indices
        self.metric_value = new_value
        self.is_finished = (not successfuly_shrinked) or len(self.current_indices) <= 2
        if not self.is_finished:
            self.iteration += 1
            self.plot_data.left_series[self.main_calc_info.label()].append(
                self.metric_value
            )

            compare_metric_value = self.compare_metric_value_for_remaining_texts()
            self.plot_data.right_series[self.compare_calc_info.label()].append(
                compare_metric_value
            )

            self.texts_count_per_iter.append(len(self.current_indices))

        self.tests_runner_folder.copy_files(self.filtered_file_paths)
        self.tests_runner.execute()
        current_errors_count = TestsRunnerResult(self.report_file_path).read_result()
        self.errors_count_per_iteration.append(current_errors_count)

    def plot_info(self) -> PercentageFilterPlotInfo:
        return PercentageFilterPlotInfo(
            iterations=self.iteration,
            texts_count_per_iter=self.texts_count_per_iter,
            main_metric_label=self.main_calc_info.label(),
            main_metric_values=self.plot_data.left_series[self.main_calc_info.label()],
            main_metric_color=self.main_calc_info.distances.algo.color,
            compare_metric_label=self.compare_calc_info.label(),
            compare_metric_values=self.plot_data.right_series[
                self.compare_calc_info.label()
            ],
            compare_metric_color=self.compare_calc_info.distances.algo.color,
            left_y_name=self.plot_data.left_y_name,
            right_y_name=self.plot_data.right_y_name,
        )
