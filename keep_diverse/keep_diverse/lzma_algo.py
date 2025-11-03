from .text_distance_algo import TextDistanceAlgo

from textdistance import LZMANCD


class LZMAAlgo(TextDistanceAlgo):

    def __init__(self):
        super().__init__("LZMANCD")

    def distance(self, text1: str, text2: str) -> float:
        return LZMANCD().distance(text1, text2)
