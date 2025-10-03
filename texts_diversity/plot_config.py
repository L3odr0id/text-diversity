from typing import List
from matplotlib.axes import Axes

from texts_diversity.calc_info import CalcInfo


class PlotConfig:
    def __init__(
        self,
        name: str,
        calc_infos: List[CalcInfo],
        axes: List[Axes],
    ):
        self.name = name
        self.calc_infos = calc_infos
        self.axes = axes
