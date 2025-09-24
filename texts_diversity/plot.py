from dataclasses import dataclass
from typing import Any, List, Dict


@dataclass
class Plot:
    ax: Any
    x_values: List[int]
    series: Dict[str, List[float]]
    y_name: str
    title: str
    x_name: str

    def draw(self):
        for label, y_values in self.series.items():
            self.ax.plot(self.x_values, y_values, marker="o", linewidth=1, label=label)
        self.ax.set_xlabel(self.x_name)
        self.ax.set_ylabel(self.y_name)
        self.ax.set_title(self.title)
        self.ax.grid(True, linestyle=":", linewidth=0.5)
        self.ax.legend(loc="best")
