import matplotlib.pyplot as plt
import shutil
import tempfile
import os


def save_plot_safely(fig: plt.Figure, output_file: str, dpi: int = 150) -> None:
    """
    Save a matplotlib figure to a file using a temporary file to avoid corruption if interrupted.
    """
    # Create a temporary file to avoid corruption if interrupted
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = tmp_file.name
    try:
        fig.savefig(tmp_path, dpi=dpi, bbox_inches="tight")
        shutil.copy2(tmp_path, output_file)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        plt.close(fig)  # Close the figure to free memory
