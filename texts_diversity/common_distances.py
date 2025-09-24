from textdistance import Levenshtein
from texts_diversity.files_list import FilesList


def always_0(a: str, b: str):
    return 0


def always_1(a: str, b: str):
    return 1


class LevenshteinDistanceNormalized:
    def __init__(self, files_list: FilesList):
        self.name = "Levenshtein Distance Normalized"
        self.max_text_length = 1
        files_list.for_each(self.find_max_text_length)

    def find_max_text_length(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        if len(text) > self.max_text_length:
            self.max_text_length = len(text)

    def distance(self, a: str, b: str) -> float:
        return Levenshtein().distance(a, b) / self.max_text_length
