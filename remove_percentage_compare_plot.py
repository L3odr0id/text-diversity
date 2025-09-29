from typing import List

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from remove_percentage_compare_metric import (
    PercentageFilterPlotInfo,
    RemovePercentageCompareFilter,
)
from texts_diversity.utils import save_plot_safely


class RemovePercentageComparePlot:
    def __init__(self, filters: List[RemovePercentageCompareFilter], output_file: str):
        self.filters = filters
        self.output_file = output_file
        print(f"RemovePercentageComparePlot initialized with {len(filters)} filters.")

    def draw(self, fig, ax1, ax2):
        while not all(f.is_finished for f in self.filters):
            for f in self.filters:
                if not f.is_finished:
                    f.iterate()

            plot_infos = [f.plot_info() for f in self.filters]

            def plot_data(ax, y_label, title, y_value_func, label_func):
                ax.clear()  # TODO: improve perfomance. Add just a new series value instead of clearing the plot

                for plot_info in plot_infos:
                    iterations = list(range(plot_info.iterations + 1))
                    ax.plot(
                        iterations,
                        y_value_func(plot_info),
                        marker="o",
                        linewidth=2,
                        label=label_func(plot_info),
                    )

                ax.set_xlabel("Iteration")
                ax.set_ylabel(y_label)
                ax.set_title(title)
                ax.grid(True, linestyle=":", linewidth=0.5)
                ax.legend(loc="best")
                ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

            plot_data(
                ax1,
                "Metric Value",
                "Metric Value vs Iteration",
                lambda plot_info: plot_info.metric_values_per_iter,
                lambda plot_info: f"{plot_info.metric_name} + {plot_info.algo_name}",
            )

            plot_data(
                ax2,
                "Number of texts",
                "Texts Count vs Iteration",
                lambda plot_info: plot_info.texts_count_per_iter,
                lambda plot_info: f"{plot_info.metric_name} x {plot_info.algo_name}",
            )

            plt.tight_layout()
            save_plot_safely(fig, self.output_file)
