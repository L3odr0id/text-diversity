from typing import List
import random
import logging

from texts_diversity.algo import Algo
from texts_diversity.texts_distances import TextsDistances, build_text_distances
from texts_diversity.calc_info import CalcInfo
from texts_diversity.metric import Metric
from src.pct_filter.pct_filter import PctFilter


class SetsSplit2:
    def __init__(
        self,
        all_file_names: List[str],
        split_by: int,
        algo: Algo,
        metric: Metric,
        relative_eps: float = 0.00001,
        max_tries: int = 10,
        min_indices_count: int = 10,
    ):
        self.current_file_names = all_file_names
        self.split_by = split_by
        self.algo = algo
        self.metric = metric
        self.relative_eps = relative_eps
        self.max_tries = max_tries
        self.min_indices_count = min_indices_count
        self.max_metric_value = -1

    def process_one_set(self, calc_info: CalcInfo, file_paths: List[str]) -> List[str]:
        initial_indices = list(range(len(file_paths)))
        pct_filter = PctFilter(
            initial_indices=initial_indices,
            relative_eps=self.relative_eps,
            max_tries=self.max_tries,
            min_indices_count=self.min_indices_count,
            intial_metric_value=self.max_metric_value,
            calc_info=calc_info,
        )

        while not pct_filter.is_finished:
            pct_filter.iterate()

        logging.info(
            f"Initial metric: {self.max_metric_value}, filtered metric: {pct_filter.current_metric_value}. Initial files num: {len(initial_indices)}, filtered files num: {len(pct_filter.current_idxs)}"
        )

        missing_indices = [
            idx for idx in initial_indices if idx not in pct_filter.current_idxs
        ]
        files_to_remove = [file_paths[idx] for idx in missing_indices]
        return files_to_remove

    def filter_files(self) -> bool:
        finished = False
        old_files_num = len(self.current_file_names)

        random.shuffle(self.current_file_names)

        smaller_sets = []
        for i in range(0, len(self.current_file_names), self.split_by):
            subset = self.current_file_names[i : i + self.split_by]
            smaller_sets.append(subset)

        logging.info(f"Made substes with lens: {[len(s) for s in smaller_sets]}")

        calc_infos = []
        for file_paths in smaller_sets:
            text_distances, _ = build_text_distances(file_paths, self.algo)
            calc_info = CalcInfo(metric=self.metric, algo=self.algo)
            calc_info.distances = text_distances
            calc_infos.append(calc_info)
            initial_metric_value = calc_info.current_value()
            if initial_metric_value > self.max_metric_value:
                self.max_metric_value = initial_metric_value
                logging.info(
                    f"Found value: {initial_metric_value}. Max: {self.max_metric_value}"
                )

        for i in range(len(smaller_sets)):
            files_set = smaller_sets[i]
            calc_info = calc_infos[i]
            files_to_remove = self.process_one_set(calc_info, files_set)

            for file_to_remove in files_to_remove:
                if file_to_remove in self.current_file_names:
                    self.current_file_names.remove(file_to_remove)

            logging.info(
                f"Removed {len(files_to_remove)} files from a set of {len(files_set)} files."
            )

        new_files_num = len(self.current_file_names)
        if new_files_num == old_files_num or new_files_num <= self.split_by:
            finished = True

        logging.info(f"Filtered from {old_files_num} to {new_files_num} files")

        return finished
