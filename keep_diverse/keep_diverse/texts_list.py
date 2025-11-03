from typing import List


class TextsList:
    def __init__(self):
        self.texts: List[str] = []

    def append(self, text: str):
        self.texts.append(text)
