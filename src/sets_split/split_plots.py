from collections import Counter
import logging

import matplotlib.pyplot as plt

from src.sets_split.sets_split_mark import SetsSplitMark
from texts_diversity.utils import save_plot_safely
from src.basic.counter_report import CounterReport


class SplitPlots:
    def __init__(
        self,
        sets_split: SetsSplitMark,
        output_file: str,
        counter_report_file: str,
        max_iter: int,
    ):
        self.sets_split = sets_split
        self.max_iter = max_iter
        self.iter = 0
        self.output_file = output_file

        self.removes_counter = Counter()
        for file_name in sets_split.current_file_names:
            self.removes_counter[file_name] = 0
        self.counter_report = CounterReport(counter_report_file)
        self.counter_report.set_counter(self.removes_counter)

    def draw_all(self):
        while self.iter < self.max_iter:
            files_to_remove = self.sets_split.filter_files()
            self.removes_counter.update(files_to_remove)

            self.iter += 1
            logging.info(f"Finished iteration {self.iter}")
            self.draw()
            self.counter_report.save()

    def draw(self):
        fig, ax1 = plt.subplots(1, 1, figsize=(25, 12))

        all_names = self.sets_split.current_file_names
        file_indices = list(range(len(all_names)))
        counts = [self.removes_counter.get(all_names[idx], 0) for idx in file_indices]

        sorted_data = sorted(
            zip(file_indices, counts), key=lambda x: x[1], reverse=True
        )
        sorted_indices, sorted_counts = zip(*sorted_data)

        x_positions = list(range(len(sorted_counts)))
        ax1.bar(x_positions, sorted_counts, width=0.5)
        ax1.set_xlabel("Files (sorted by count)")
        ax1.set_ylabel("Times to remove")
        ax1.set_yticks(range(max(sorted_counts) + 1))

        ax1.set_xticks(x_positions)
        ax1.set_xticklabels(sorted_indices, rotation=45, ha="right")
        ax1.tick_params(axis="x", which="major", pad=10)
        ax1.set_title(
            f"Times to remove count. Iter {self.iter}. Files: {len(all_names)}. Split by: {self.sets_split.split_by}"
        )

        plt.tight_layout(pad=3.0)
        save_plot_safely(fig, self.output_file)
