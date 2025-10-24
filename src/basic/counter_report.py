import json
from collections import Counter


class CounterReport:
    def __init__(self, output_file: str):
        self.output_file = output_file

    def set_counter(self, counter: Counter):
        self.counter = counter

    def load_counter(self):
        with open(self.output_file, "r") as f:
            self.counter = Counter(json.load(f))

    def save(self):
        with open(self.output_file, "w") as f:
            json.dump(dict(self.counter), f, indent=2)
