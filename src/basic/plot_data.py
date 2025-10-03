from dataclasses import dataclass
from typing import List, Dict


@dataclass
class PlotData:
    x_values: List[int]
    x_name: str
    left_series: Dict[str, List[float]]
    left_y_name: str
    right_series: Dict[str, List[float]]
    right_y_name: str
    title: str
