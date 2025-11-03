import json
from collections import Counter


class MarksToRemoveList:
    def __init__(self, output_file: str):
        self.output_file = output_file

    def save(self, counter: Counter):
        with open(self.output_file, "w") as f:
            json.dump(dict(counter), f, indent=2)
