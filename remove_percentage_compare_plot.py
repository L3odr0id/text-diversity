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
        pct_filter: RemovePercentageCompareFilter,
        output_file: str,
        errors_report_file_path: str,
    ):
        self.pct_filter = pct_filter
        self.output_file = output_file
        self.errors_report_file_path = errors_report_file_path
        self.ax2 = None  # Store twin axis to avoid duplication. Very bad code because matplotlib has an awful interface

    def plot_metrics_comparison(self, ax):
        """Plot main and compare metrics on dual y-axis"""
        ax.clear()  # TODO: perfomance. Add just a new series value instead of clearing the plot

        plot_info = self.pct_filter.plot_info()
        iterations = list(range(plot_info.iterations + 1))

        if self.ax2 is None:
            self.ax2 = ax.twinx()
        else:
            self.ax2.clear()

        line1 = ax.plot(
            iterations,
            plot_info.main_metric_values,
            color=plot_info.main_metric_color,
            label=plot_info.main_metric_label,
        )

        line2 = self.ax2.plot(
            iterations,
            plot_info.compare_metric_values,
            color=plot_info.compare_metric_color,
            label=plot_info.compare_metric_label,
        )

        ax.set_xlabel("Filter iteration")
        ax.set_ylabel(plot_info.left_y_name, color=plot_info.main_metric_color)
        self.ax2.set_ylabel(
            plot_info.right_y_name, color=plot_info.compare_metric_color
        )
        ax.set_title("Main vs Compare metric values")
        ax.grid(True, linestyle=":", linewidth=0.5)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

        ax.tick_params(axis="y", labelcolor=plot_info.main_metric_color)
        self.ax2.tick_params(axis="y", labelcolor=plot_info.compare_metric_color)

        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc="best")

    def plot_texts_count(self, ax):
        """Plot texts count vs iteration"""
        ax.clear()

        plot_info = self.pct_filter.plot_info()
        iterations = list(range(plot_info.iterations + 1))

        ax.plot(
            iterations,
            plot_info.texts_count_per_iter,
            marker="o",
            linewidth=2,
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
        errors_count: List[ErrorsCount],
        count_field: str,
        ylabel: str,
        title: str,
    ):
        ax.clear()

        original_errors_count = self.pct_filter.original_errors_count

        sorted_errors = sorted(errors_count, key=lambda x: x.error_id)
        error_ids = [error.error_id for error in sorted_errors]
        current_counts = [getattr(error, count_field) for error in sorted_errors]

        original_counts = []
        for error_id in error_ids:
            original_error = next(
                (e for e in original_errors_count if e.error_id == error_id), None
            )
            original_counts.append(
                getattr(original_error, count_field) if original_error else 0
            )

        x_positions = range(len(error_ids))
        bar_width = 0.35

        ax.bar(
            [x - bar_width / 2 for x in x_positions],
            original_counts,
            width=bar_width,
            alpha=0.8,
            color="mediumslateblue",
            label="Full set",
        )

        ax.bar(
            [x + bar_width / 2 for x in x_positions],
            current_counts,
            width=bar_width,
            alpha=0.8,
            color="tomato",
            label="Last iteration",
        )

        ax.set_xlabel("Error ID")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, linestyle=":", linewidth=0.5, axis="y")
        ax.legend()

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

        ax.set_xticks(x_positions)
        ax.set_xticklabels(error_ids)

    def draw(self, fig, ax1, ax2, ax3, ax4):
        while not self.pct_filter.is_finished:
            if not self.pct_filter.is_finished:
                self.pct_filter.iterate()

            self.plot_metrics_comparison(ax1)

            self.plot_texts_count(ax2)

            errors_count = TestsRunnerResult(self.errors_report_file_path).read_result()
            self.draw_errors_count(
                ax3,
                errors_count,
                "test_paths_count",
                "Number of test files with error",
                "Errors Count vs Error ID (Test files)",
            )

            self.draw_errors_count(
                ax4,
                errors_count,
                "overall",
                "Overall error count",
                "Errors Count vs Error ID (Overall)",
            )

            plt.tight_layout()
            save_plot_safely(fig, self.output_file)
