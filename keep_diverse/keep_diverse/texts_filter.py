import logging
from collections import Counter
from concurrent.futures import as_completed
import multiprocessing

from .split_sets_mark import SplitSetsMark
from .marks_to_remove_list import (
    MarksToRemoveList,
)
from .knee_plot import KneePlot
from .knee import Knee
from .filtered_files_list import (
    FilteredFilesList,
)
from .process_pool_utils import safe_process_pool_executor


def _call_filter_files(sets_split: SplitSetsMark):
    """Standalone function to call filter_files for parallel execution"""
    return sets_split.filter_files()


class TextsFilter:
    def __init__(
        self,
        sets_split: SplitSetsMark,
        knee_plot: KneePlot,
        filtered_files_list: FilteredFilesList,
        max_iter: int,
        max_workers: int,
    ):
        self.sets_split = sets_split
        self.max_iter = max_iter
        self.knee_plot = knee_plot
        self.filtered_files_list = filtered_files_list
        self.max_workers = max_workers

        self.finished_rounds = 0

        self.removes_counter = Counter()
        for file_name in sets_split.current_file_names:
            self.removes_counter[file_name] = 0
        self.artifacts_lock = multiprocessing.Lock()

    def produce_artifacts(self):
        knee = Knee(self.removes_counter)
        self.knee_plot.draw(knee, self.finished_rounds)
        self.filtered_files_list.save(knee)

    def process(self):
        with safe_process_pool_executor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(_call_filter_files, self.sets_split): i
                for i in range(self.max_iter)
            }

            for future in as_completed(futures):
                files_to_remove = future.result()

                with self.artifacts_lock:
                    self.finished_rounds += 1
                    self.removes_counter.update(files_to_remove)
                    self.produce_artifacts()
