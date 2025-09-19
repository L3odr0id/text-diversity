import matplotlib.pyplot as plt
import shutil
import tempfile
import os
from typing import List, Dict, Tuple, Optional

from texts_diversity.plot_config import PlotConfig
from texts_diversity.plot import Plot


class PlotsList:
    def __init__(self, configs: List[PlotConfig], title: str, output_file: str):
        self.configs = configs
        self.x_values = []
        self.y_values = {
            plot_config.metric.name: {
                td.algo.name: [] for td in plot_config.texts_distances
            }
            for plot_config in configs
        }
        self.title = title
        self.output_file = output_file

    def add_x_value(self, x_value: int):
        self.x_values.append(x_value)

    def add_y_values(self):
        for plot_config in self.configs:
            for texts_distance in plot_config.texts_distances:
                y_value = plot_config.metric.calc(texts_distance)
                self.y_values[plot_config.metric.name][texts_distance.algo.name].append(
                    y_value
                )

    def draw(self):
        num_plots = max(1, len(self.configs))
        fig, axes = plt.subplots(1, num_plots, figsize=(10 * num_plots, 6))
        if num_plots == 1:
            axes = [axes]
        for idx, (plot_config, (y_name, series)) in enumerate(
            zip(self.configs, self.y_values.items())
        ):
            plot = Plot(
                ax=axes[idx],
                x_values=self.x_values,
                series=series,
                y_name=y_name,
                title=plot_config.name,
            )
            plot.draw()

        fig.suptitle(self.title)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        # Create a temporary file to avoid corruption if interrupted
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        try:
            fig.savefig(tmp_path, dpi=150, bbox_inches="tight")
            shutil.copy2(tmp_path, self.output_file)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            plt.close(fig)  # Close the figure to free memory
