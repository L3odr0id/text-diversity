import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Optional, Tuple


def draw_one_plot(ax, x_values: List[int], series: Dict[str, List[float]], y_name: str, title: Optional[str] = None, normalize: bool = False) -> None:
    for label, y_values in series.items():
        new_y_values = y_values
        if normalize:
            # Min-max normalization: normalized = (x - min(x)) / (max(x) - min(x))
            y_array = np.array(y_values)
            min_y = np.nanmin(y_array)
            max_y = np.nanmax(y_array)
            if max_y != min_y:  # Avoid division by zero
                new_y_values = (y_array - min_y) / (max_y - min_y)
                new_y_values = new_y_values.tolist()
            else:
                new_y_values = y_values  # Keep original values if all values are the same
        
        ax.plot(x_values, new_y_values, marker="o", linewidth=1, label=label)
    ax.set_xlabel("Number of files")
    ax.set_ylabel(y_name)
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.legend()


def draw_all_plots(x_values: List[int], plots: List[Tuple[str, Dict[str, List[float]], bool]], title: Optional[str] = None, output_path: Optional[str] = None) -> None:
    num_plots = max(1, len(plots))
    fig, axes = plt.subplots(1, num_plots, figsize=(6 * num_plots, 5))
    if num_plots == 1:
        axes = [axes]
    for idx, (y_name, series, normalize) in enumerate(plots):
        draw_one_plot(axes[idx], x_values, series, y_name=y_name, normalize=normalize)
    if title:
        fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    if output_path:
        fig.savefig(output_path, dpi=250)
    else:
        plt.show()


