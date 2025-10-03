from typing import List

from texts_diversity.plot_config import PlotConfig
from texts_diversity.plot import Plot
from texts_diversity.utils import save_plot_safely


class PlotsList:
    def __init__(self, configs: List[PlotConfig], title: str, output_file: str, fig):
        self.configs = configs
        self.x_values = []
        self.y_values = {
            plot_config: {calc_info: [] for calc_info in plot_config.calc_infos}
            for plot_config in configs
        }
        self.title = title
        self.output_file = output_file
        self.fig = fig

    def add_x_value(self, x_value: int):
        self.x_values.append(x_value)

    def add_y_values(self):
        for plot_config in self.configs:
            for calc_info in plot_config.calc_infos:
                y_value = calc_info.metric.calc(calc_info.distances)
                print(
                    f"Metric {calc_info.metric.name}. Algo: {calc_info.distances.algo.name}. Value: {y_value}. For {self.x_values[-1]} texts"
                )
                self.y_values[plot_config][calc_info].append(y_value)

    def draw(self):
        fig = self.fig

        for plot_config in self.configs:
            # Group series by axis to avoid overriding
            axis_series = {}
            axis_series_colors = {}

            for idx, calc_info in enumerate(plot_config.calc_infos):
                ax = plot_config.axes[idx]
                ax_id = id(ax)

                if ax_id not in axis_series:
                    axis_series[ax_id] = {}
                    axis_series_colors[ax_id] = {}

                label = f"{calc_info.metric.name} ({calc_info.distances.algo.name})"
                axis_series[ax_id][label] = self.y_values[plot_config][calc_info]
                axis_series_colors[ax_id][label] = calc_info.distances.algo.color

            for ax_id, series in axis_series.items():
                ax = None
                for idx, calc_info in enumerate(plot_config.calc_infos):
                    if id(plot_config.axes[idx]) == ax_id:
                        ax = plot_config.axes[idx]
                        break

                if ax is not None:
                    plot = Plot(
                        ax=ax,
                        x_values=self.x_values,
                        x_name="Number of files",
                        series=series,
                        y_name="Metric values",
                        title=plot_config.name,
                        series_colors=axis_series_colors[ax_id],
                    )
                    plot.draw()

        fig.suptitle(self.title)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])

        save_plot_safely(fig, self.output_file)
