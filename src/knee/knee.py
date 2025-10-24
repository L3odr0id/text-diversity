from typing import List

import matplotlib.pyplot as plt
from kneed import KneeLocator

from texts_diversity.utils import save_plot_safely


class Knee:
    def __init__(self, x_values: List[int], y_values: List[float]):
        self.x_values = x_values
        self.y_values = y_values

    def find_knee(self):
        kneedle = KneeLocator(
            self.x_values, self.y_values, S=1.0, curve="concave", direction="decreasing"
        )
        print(f"Knee point: {kneedle.knee}")
        return round(kneedle.knee, 3)

    def draw(self, output_file: str):
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(self.x_values, self.y_values, "b-", linewidth=2, label="Data")

        knee_point = self.find_knee()

        ax.axvline(
            x=knee_point,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Knee point: {knee_point}",
        )

        ax.set_xlabel("X Values")
        ax.set_ylabel("Y Values")
        ax.set_title("Knee Detection Plot")
        ax.legend()
        ax.grid(True, alpha=0.3)

        save_plot_safely(fig, output_file)
