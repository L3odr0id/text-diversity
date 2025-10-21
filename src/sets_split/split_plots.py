from collections import Counter

import matplotlib.pyplot as plt

from src.sets_split.sets_split_mark import SetsSplitMark
from texts_diversity.utils import save_plot_safely


class SplitPlots:
    def __init__(self, sets_split: SetsSplitMark, output_file: str, max_iter: int):
        self.sets_split = sets_split
        self.max_iter = max_iter
        self.iter = 0
        self.removes_counter = Counter()
        self.output_file = output_file

    def draw_all(self):
        while self.iter < self.max_iter:
            files_to_remove = self.sets_split.filter_files()
            self.removes_counter.update(files_to_remove)
            print(
                f"Removed {len(files_to_remove)} files. Files: {len(self.sets_split.current_file_names)}. Split by: {self.sets_split.split_by}. Counter {self.removes_counter}"
            )
            self.iter += 1
            self.draw()

    def draw(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(25, 12))

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

        max_count = max(self.removes_counter.values())
        count_distribution = {}
        for count_value in range(max_count + 1):
            count_distribution[count_value] = counts.count(count_value)

        labels = [f"{count} times" for count in count_distribution.keys()]
        sizes = list(count_distribution.values())
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=None, autopct="%1.1f%%", startangle=90
        )
        ax2.legend(
            wedges,
            labels,
            title="Remove Count",
            loc="upper right",
            bbox_to_anchor=(1, 0, 0.5, 1),
        )

        ax2.set_title(
            f"Distribution of remove counts. Iter {self.iter}. Files: {len(all_names)}. Split by: {self.sets_split.split_by}"
        )

        plt.tight_layout(pad=3.0)
        save_plot_safely(fig, self.output_file)
