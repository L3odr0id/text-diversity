from typing import List

from texts_diversity.calc_info import CalcInfo


class PlotConfig:
    def __init__(self, name: str, calc_infos: List[CalcInfo]):
        self.name = name
        self.calc_infos = calc_infos
