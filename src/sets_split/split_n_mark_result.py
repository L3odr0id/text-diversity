import logging
from collections import Counter

from src.sets_split.sets_split_mark import SetsSplitMark
from src.basic.counter_report import CounterReport


class SplitMarkResult:
    def __init__(
        self,
        sets_split: SetsSplitMark,
        counter_report_file_path: str,
        max_iter: int,
    ):
        self.sets_split = sets_split
        self.max_iter = max_iter
        self.iter = 0

        self.removes_counter = Counter()
        for file_name in sets_split.current_file_names:
            self.removes_counter[file_name] = 0
        self.counter_report = CounterReport(counter_report_file_path)
        self.counter_report.set_counter(self.removes_counter)

    def process(self):
        while self.iter < self.max_iter:
            files_to_remove = self.sets_split.filter_files()
            self.removes_counter.update(files_to_remove)

            self.iter += 1
            logging.info(f"Finished iteration {self.iter}")
            self.counter_report.save()
