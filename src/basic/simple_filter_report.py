from typing import List


class SimpleFilterReport:
    def __init__(self, output_file: str, good_file_names: List[str]):
        self.output_file = output_file
        self.good_file_names = good_file_names

    def save(self):
        content = "\n".join(self.good_file_names)
        with open(self.output_file, "w") as f:
            f.write(content)
