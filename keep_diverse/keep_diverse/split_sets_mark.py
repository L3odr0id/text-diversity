import os
from typing import List
import random
import logging
from concurrent.futures import as_completed

from .text_distance_algo import TextDistanceAlgo
from .texts_list import TextsList
from .text_set_distances_list import (
    TextSetDistancesList,
)
from .text_set_diversity_metric import (
    TextSetDiversityMetric,
)
from .pct_filter import PctFilter
from .process_pool_utils import safe_process_pool_executor


def process_one_set(
    file_paths: List[str],
    algo: TextDistanceAlgo,
    metric: TextSetDiversityMetric,
    relative_eps: float,
    max_tries: int,
    min_indices_count: int,
) -> List[str]:
    text_distances = TextSetDistancesList(algo=algo, texts=TextsList())
    text_distances.init_texts(file_paths)
    initial_metric_value = metric.value(text_distances)
    initial_indices = list(range(len(file_paths)))

    pct_filter = PctFilter(
        initial_indices=initial_indices,
        text_set_distances=text_distances,
        metric=metric,
        relative_eps=relative_eps,
        max_tries=max_tries,
        min_indices_count=min_indices_count,
    )

    while not pct_filter.is_finished:
        pct_filter.iterate()

    logging.info(
        f"Initial metric: {initial_metric_value}, filtered metric: {pct_filter.current_metric_value}. Initial files num: {len(file_paths)}, filtered files num: {len(pct_filter.current_idxs)}"
    )

    missing_indices = [
        idx for idx in initial_indices if idx not in pct_filter.current_idxs
    ]
    files_to_remove = [file_paths[idx] for idx in missing_indices]
    return files_to_remove


class SplitSetsMark:
    def __init__(
        self,
        all_file_names: List[str],
        split_by: int,
        algo: TextDistanceAlgo,
        metric: TextSetDiversityMetric,
        relative_eps: float = 0.00001,
        max_tries: int = 10,
        min_indices_count: int = 10,
        max_workers: int = os.cpu_count(),
    ):
        self.current_file_names = all_file_names
        self.split_by = split_by
        self.algo = algo
        self.metric = metric
        self.relative_eps = relative_eps
        self.max_tries = max_tries
        self.min_indices_count = min_indices_count
        self.max_workers = max_workers

    def filter_files(self):
        random.shuffle(self.current_file_names)

        smaller_sets = []
        for i in range(0, len(self.current_file_names), self.split_by):
            subset = self.current_file_names[i : i + self.split_by]
            smaller_sets.append(subset)

        logging.info(
            f"Made {len(smaller_sets)} substes with lens: {[len(s) for s in smaller_sets]}"
        )

        all_files_to_remove = []

        with safe_process_pool_executor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    process_one_set,
                    files_set,
                    self.algo,
                    self.metric,
                    self.relative_eps,
                    self.max_tries,
                    self.min_indices_count,
                )
                for files_set in smaller_sets
            ]

            for future in as_completed(futures):
                files_to_remove = future.result()
                all_files_to_remove.extend(files_to_remove)
                logging.info(f"Marked {len(files_to_remove)} files to remove")

        logging.info(f"Finished iteration")

        return all_files_to_remove
