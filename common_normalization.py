from typing import List
import numpy as np

def min_max_normalization(y_values: List[float]) -> List[float]:
    """
    Min-max normalization: normalized = (x - min(x)) / (max(x) - min(x))
    """
    y_array = np.array(y_values)
    min_y = np.nanmin(y_array)
    max_y = np.nanmax(y_array)
    diff = max_y - min_y
    if diff != 0:
        new_y_values = (y_array - min_y) / (diff)
        return new_y_values.tolist()
    else:
        return y_values
