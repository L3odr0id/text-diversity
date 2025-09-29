from typing import List

import matplotlib.pyplot as plt

from texts_diversity.files_list import FilesList
from texts_diversity.plot import Plot
from texts_diversity.utils import save_plot_safely
from TDSMetric import TDSMetric


class TDSMetricPlot:
    def __init__(
        self, files_list: FilesList, metrics: List[TDSMetric], output_file: str
    ):
        self.files_list = files_list
        self.metrics = metrics
        self.texts = []
        self.y_values = {metric.algo.name: [] for metric in self.metrics}
        self.x_values = []
        self.output_file = output_file

    def make_plot(self):
        self.files_list.for_each(self.process_file)

    def process_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            new_file_content = f.read()

        self.texts.append(new_file_content)

        if len(self.texts) < 2:
            return

        self.x_values.append(len(self.texts))

        for metric in self.metrics:
            result = metric.NCD1(self.texts)
            self.y_values[metric.algo.name].append(result)

        self.draw()

    def draw(self):
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))

        series = {}
        for metric in self.metrics:
            series[metric.algo.name] = self.y_values[metric.algo.name]

        plot = Plot(
            ax=ax,
            x_values=self.x_values,
            series=series,
            y_name="TDS Metric Value",
            title="TDS Metric vs Number of Texts",
            x_name="Number of Texts",
        )

        plot.draw()

        save_plot_safely(fig, self.output_file)
