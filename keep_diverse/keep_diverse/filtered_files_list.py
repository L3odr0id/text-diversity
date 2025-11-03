from .knee import Knee


class FilteredFilesList:
    def __init__(self, output_file_path: str):
        self.output_file_path = output_file_path

    def save(self, knee: Knee):
        content = "\n".join(knee.good_files())
        with open(self.output_file_path, "w") as f:
            f.write(content)
