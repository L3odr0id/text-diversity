from typing import List

import matplotlib.pyplot as plt
from kneed import KneeLocator

from texts_diversity.utils import save_plot_safely


class Knee:
    def __init__(self, x_values: List[int], y_values: List[float]):
        self.x_values = x_values
        self.y_values = y_values

    def find_knee(self) -> float:
        kneedle = KneeLocator(
            self.x_values,
            self.y_values,
            S=1,
            curve="concave",
            direction="decreasing",
            interp_method="polynomial",
            polynomial_degree=3,
        )
        print(f"Knee point: {kneedle.knee}")
        return round(kneedle.knee, 3)

    def draw_self(self, output_file: str) -> None:
        fig, ax = plt.subplots(figsize=(10, 6))
        self.draw(ax=ax)
        save_plot_safely(fig, output_file)

    def draw(self, ax: plt.Axes):
        ax.clear()
        ax.plot(self.x_values, self.y_values, "b-", linewidth=2, label="Data")

        knee_point = self.find_knee()

        ax.axvline(
            x=knee_point,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Knee point: {knee_point}",
        )

        ax.set_xlabel("Files")
        ax.set_ylabel("Times to remove")
        ax.set_title("Knee Detection Plot")
        ax.legend()
        ax.grid(True, alpha=0.3)
