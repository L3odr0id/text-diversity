import logging

from src.sets_split.sets_split import SetsSplit


class SplitFilterResults:
    def __init__(self, sets_split: SetsSplit) -> None:
        self.sets_split = sets_split

    def process(self, output_file_path: str):
        finished = False
        while not finished:
            finished = self.sets_split.filter_files()
            content = "".join(
                f"{file_name}\n" for file_name in self.sets_split.current_file_names
            )
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(content)

            logging.info(
                f"{len(self.sets_split.current_file_names)} file names are written to {output_file_path}"
            )
