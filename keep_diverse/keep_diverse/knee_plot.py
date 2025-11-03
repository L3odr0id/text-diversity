from typing import List
from dataclasses import dataclass

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from .save_plot_safely import save_plot_safely
from .knee import Knee


@dataclass
class DisplayKneeArgs:
    total_files_count: int
    split_by: int
    relative_eps: float
    max_tries: int
    min_indices_count: int
    filter_rounds: int

    def to_string(self) -> str:
        return f"/{self.filter_rounds} rounds. Total files count: {self.total_files_count}. Split by: {self.split_by}. Relative eps: {self.relative_eps}. Max tries: {self.max_tries}. Min indices count: {self.min_indices_count}."


class KneePlot:
    def __init__(self, output_file: str, display_knee_args: DisplayKneeArgs):
        self.output_file = output_file
        self.display_knee_args = display_knee_args

    def draw(self, knee: Knee, round_number: int):
        fig, ax = plt.subplots(1, 1, figsize=(10, 6))
        plt.subplots_adjust(bottom=0.2)
        ax.clear()
        ax.plot(knee.x_values, knee.y_values, "b-", linewidth=2, label="Data")

        ax.axvline(
            x=knee.value,
            color="red",
            linestyle="--",
            linewidth=2,
            label=f"Knee point: {knee.value}",
        )

        ax.set_xlabel("Files")
        ax.set_ylabel("Times to remove")
        ax.set_title("Knee Detection Plot")
        ax.legend()
        ax.grid(True, alpha=0.3)

        ax.text(
            0.5,
            -0.15,
            f"{round_number}" + self.display_knee_args.to_string(),
            transform=ax.transAxes,
            ha="center",
            fontsize=8,
            style="italic",
        )

        save_plot_safely(fig, self.output_file)
