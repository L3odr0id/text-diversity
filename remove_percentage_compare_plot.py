from typing import List

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from remove_percentage_compare_metric import (
    RemovePercentageCompareFilter,
)
from texts_diversity.utils import save_plot_safely
from tests_runner import TestsRunnerResult
from tests_runner import ErrorsCount


class RemovePercentageComparePlot:
    def __init__(
        self,
        pct_filters: List[RemovePercentageCompareFilter],
        output_file: str,
        errors_report_file_path: str,
    ):
        self.pct_filters = pct_filters
        self.output_file = output_file
        self.errors_report_file_path = errors_report_file_path
        self.ax2s = {}  # Store twin axes for each filter to avoid duplication

    def plot_metrics_comparison(self, ax, filter_idx: int):
        ax.clear()

        pct_filter = self.pct_filters[filter_idx]
        plot_info = pct_filter.plot_info()
        iterations = list(range(plot_info.iterations + 1))

        if filter_idx in self.ax2s:
            self.ax2s[filter_idx].remove()
        self.ax2s[filter_idx] = ax.twinx()

        line1 = ax.plot(
            iterations,
            plot_info.main_metric_values,
            marker="o",
            color=plot_info.main_metric_color,
            label=plot_info.main_metric_label,
        )

        line2 = self.ax2s[filter_idx].plot(
            iterations,
            plot_info.compare_metric_values,
            marker="o",
            color=plot_info.compare_metric_color,
            label=plot_info.compare_metric_label,
        )

        ax.set_xlabel("Filter iteration")
        ax.set_ylabel(plot_info.left_y_name, color=plot_info.main_metric_color)
        self.ax2s[filter_idx].set_ylabel(
            plot_info.right_y_name, color=plot_info.compare_metric_color
        )
        ax.set_title("Main vs Compare metric values")
        ax.grid(True, linestyle=":", linewidth=0.5)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

        ax.tick_params(axis="y", labelcolor=plot_info.main_metric_color)
        self.ax2s[filter_idx].tick_params(
            axis="y", labelcolor=plot_info.compare_metric_color
        )

        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc="best")

    def plot_texts_count(self, ax, filter_idx: int):
        ax.clear()

        pct_filter = self.pct_filters[filter_idx]
        plot_info = pct_filter.plot_info()
        iterations = list(range(plot_info.iterations + 1))

        ax.plot(
            iterations,
            plot_info.texts_count_per_iter,
            marker="o",
            color="green",
            label="Number of texts",
        )

        ax.set_xlabel("Filter iteration")
        ax.set_ylabel("Number of texts")
        ax.set_title("Number of texts vs Filter iteration")
        ax.grid(True, linestyle=":", linewidth=0.5)
        ax.legend(loc="best")
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    def draw_errors_count(
        self,
        ax,
        count_field: str,
        ylabel: str,
        title: str,
        iteration: int,
    ):
        ax.clear()

        original_errors_count = self.pct_filters[0].original_errors_count

        sorted_original_errors = sorted(original_errors_count, key=lambda x: x.error_id)
        error_ids = [error.error_id for error in sorted_original_errors]
        original_counts = [
            getattr(error, count_field) for error in sorted_original_errors
        ]

        initial_test_count = self.pct_filters[0].total_files_count
        original_percentages = [count / initial_test_count for count in original_counts]

        filter_percentages = []
        for pct_filter in self.pct_filters:
            if iteration < len(pct_filter.errors_count_per_iteration):
                current_test_count = len(pct_filter.current_indices)
                errors_count = pct_filter.errors_count_per_iteration[iteration]
            else:
                current_test_count = len(pct_filter.current_indices)
                errors_count = pct_filter.errors_count_per_iteration[-1]

            current_counts = []
            for error_id in error_ids:
                current_error = next(
                    (e for e in errors_count if e.error_id == error_id), None
                )
                current_counts.append(
                    getattr(current_error, count_field) if current_error else 0
                )

            current_percentages = [
                count / current_test_count for count in current_counts
            ]
            filter_percentages.append(current_percentages)

        x_positions = range(len(error_ids))

        num_available_filters = len(self.pct_filters)
        bar_width = 0.8 / (num_available_filters + 1)

        ax.bar(
            [x - (num_available_filters * bar_width / 2) for x in x_positions],
            original_percentages,
            width=bar_width,
            alpha=0.8,
            color="lavender",
            label="Full set",
        )

        for i, (pct_filter, percentages) in enumerate(
            zip(self.pct_filters, filter_percentages)
        ):
            color = pct_filter.main_calc_info.distances.algo.color
            offset = (i + 1) * bar_width - (num_available_filters * bar_width / 2)
            ax.bar(
                [x + offset for x in x_positions],
                percentages,
                width=bar_width,
                alpha=0.8,
                color=color,
                label=f"Filter by {pct_filter.main_calc_info.distances.algo.name}",
            )

        ax.set_xlabel("Error ID")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, linestyle=":", linewidth=0.5, axis="y")
        ax.legend()

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        ax.set_xticks(x_positions)
        ax.set_xticklabels(error_ids)

    def draw(self, fig, ax1s: List, ax2s: List, ax3s: List, ax4s: List):
        iteration = 0
        while not all(filter.is_finished for filter in self.pct_filters):
            if iteration != 0:
                for i, pct_filter in enumerate(self.pct_filters):
                    if not pct_filter.is_finished:
                        pct_filter.iterate()

                for i, pct_filter in enumerate(self.pct_filters):
                    self.plot_metrics_comparison(ax1s[i], i)
                    self.plot_texts_count(ax2s[i], i)

            if not all(filter.is_finished for filter in self.pct_filters):
                self.draw_errors_count(
                    ax3s[iteration],
                    "test_paths_count",
                    "Percentage of test files with error",
                    f"Errors Percentage vs Error ID (Test files). Iter {iteration}",
                    iteration,
                )

                self.draw_errors_count(
                    ax4s[iteration],
                    "overall",
                    "Overall error percentage",
                    f"Errors Percentage vs Error ID (Overall). Iter {iteration}",
                    iteration,
                )

            iteration += 1
            save_plot_safely(fig, self.output_file)
