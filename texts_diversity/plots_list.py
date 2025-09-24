import matplotlib.pyplot as plt
from typing import List, Dict, Tuple, Optional

from texts_diversity.plot_config import PlotConfig
from texts_diversity.plot import Plot
from texts_diversity.utils import save_plot_safely


class PlotsList:
    def __init__(self, configs: List[PlotConfig], title: str, output_file: str):
        self.configs = configs
        self.x_values = []
        self.y_values = {
            plot_config: {calc_info: [] for calc_info in plot_config.calc_infos}
            for plot_config in configs
        }
        self.title = title
        self.output_file = output_file

    def add_x_value(self, x_value: int):
        self.x_values.append(x_value)

    def add_y_values(self):
        for plot_config in self.configs:
            for calc_info in plot_config.calc_infos:
                y_value = calc_info.metric.calc(calc_info.distances)
                self.y_values[plot_config][calc_info].append(y_value)

    def draw(self):
        num_plots = max(1, len(self.configs))
        fig, axes = plt.subplots(1, num_plots, figsize=(10 * num_plots, 6))
        if num_plots == 1:
            axes = [axes]
        for idx, plot_config in enumerate(self.configs):

            series = {}
            for calc_info in plot_config.calc_infos:
                # Create unique label combining metric and algorithm names
                label = f"{calc_info.metric.name} ({calc_info.distances.algo.name})"
                series[label] = self.y_values[plot_config][calc_info]

            plot = Plot(
                ax=axes[idx],
                x_values=self.x_values,
                x_name="Number of files",
                series=series,
                y_name="Metric values",
                title=plot_config.name,
            )
            plot.draw()

        fig.suptitle(self.title)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        save_plot_safely(fig, self.output_file)
