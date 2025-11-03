from abc import ABC, abstractmethod


class TextDistanceAlgo(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def distance(self, text1: str, text2: str) -> float:
        pass
