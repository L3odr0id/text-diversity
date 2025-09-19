import matplotlib.pyplot as plt
import numpy as np
import shutil
import tempfile
import os
from typing import Dict, List, Optional, Tuple


def draw_one_plot(ax, x_values: List[int], series: Dict[str, List[float]], y_name: str, title: Optional[str] = None) -> None:
    for label, y_values in series.items():
        ax.plot(x_values, y_values, marker="o", linewidth=1, label=label)
    ax.set_xlabel("Number of files")
    ax.set_ylabel(y_name)
    if title:
        ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.5)
    ax.legend(loc='lower right')


def draw_all_plots(x_values: List[int], plots: List[Tuple[str, Dict[str, List[float]]]], title: Optional[str] = None, output_path: Optional[str] = None) -> None:
    num_plots = max(1, len(plots))
    fig, axes = plt.subplots(1, num_plots, figsize=(12 * num_plots, 8))
    if num_plots == 1:
        axes = [axes]
    for idx, (y_name, series) in enumerate(plots):
        draw_one_plot(axes[idx], x_values, series, y_name=y_name)
    if title:
        fig.suptitle(title)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    if output_path:
        # Create a temporary file to avoid corruption if interrupted
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        try:
            fig.savefig(tmp_path, dpi=150, bbox_inches='tight')
            shutil.copy2(tmp_path, output_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        plt.show()


