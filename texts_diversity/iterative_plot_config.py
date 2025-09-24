from typing import List
import matplotlib.pyplot as plt

from texts_diversity.plot import Plot
from texts_diversity.utils import save_plot_safely
from texts_diversity.iterative_metric import IterativeMetric


class IterativePlotConfig:
    def __init__(
        self,
        name: str,
        texts: List[str],
        metric: IterativeMetric,
        output_file: str,
    ):
        self.name = name
        self.texts = texts
        self.metric = metric
        self.output_file = output_file
        self.y_values = []

    def execute(self):
        finish = False
        while not finish:
            result = self.metric.calc(self.texts)
            self.texts = result.texts
            finish = result.finished
            self.y_values.append(result.value)
            self.draw()

    def draw(self):
        if not self.y_values:
            return

        x_values = list(range(len(self.y_values)))

        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        series = {self.metric.name: self.y_values}
        plot = Plot(
            ax=ax,
            x_values=x_values,
            x_name="Iteration",
            series=series,
            y_name=self.metric.name,
            title=self.name,
        )
        plot.draw()

        save_plot_safely(fig, self.output_file)
