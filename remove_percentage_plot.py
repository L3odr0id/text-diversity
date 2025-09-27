from typing import List

import matplotlib.pyplot as plt

from remove_percentage_metric import PercentageFilterPlotInfo, RemovePercentageMetric
from texts_diversity.utils import save_plot_safely


class RemovePercentagePlot:
    def __init__(self, filters: List[RemovePercentageMetric], output_file: str):
        self.filters = filters
        self.output_file = output_file
        print(f"RemovePercentagePlot initialized with {len(filters)} filters.")

    def draw(self):
        # Run iterations until all filters are finished
        while not all(f.is_finished for f in self.filters):
            for f in self.filters:
                if not f.is_finished:
                    f.iterate()

            # Collect plot info from all filters
            plot_infos = [f.plot_info() for f in self.filters]

            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            # Plot 1: Files count vs iteration
            for plot_info in plot_infos:
                iterations = list(range(plot_info.iterations + 1))
                ax1.plot(
                    iterations,
                    plot_info.texts_count_per_iter,
                    marker="o",
                    linewidth=2,
                    label=f"{plot_info.metric_name} x {plot_info.algo_name}",
                )

            ax1.set_xlabel("Iteration")
            ax1.set_ylabel("Number of texts")
            ax1.set_title("Texts Count vs Iteration")
            ax1.grid(True, linestyle=":", linewidth=0.5)
            ax1.legend(loc="best")

            # Plot 2: Metric values vs iteration
            for plot_info in plot_infos:
                iterations = list(range(plot_info.iterations + 1))
                ax2.plot(
                    iterations,
                    plot_info.metric_values_per_iter,
                    marker="o",
                    linewidth=2,
                    label=f"{plot_info.metric_name} + {plot_info.algo_name}",
                )

            ax2.set_xlabel("Iteration")
            ax2.set_ylabel("Metric Value")
            ax2.set_title("Metric Value vs Iteration")
            ax2.grid(True, linestyle=":", linewidth=0.5)
            ax2.legend(loc="best")

            # Adjust layout and save
            plt.tight_layout()
            save_plot_safely(fig, self.output_file)
