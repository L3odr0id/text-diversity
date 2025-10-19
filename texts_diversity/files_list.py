import os
import random
from typing import List, Callable


class FilesList:
    def __init__(self, files_dir: str, shuffle: bool, max_files: int):
        self.file_paths = self._get_file_paths(files_dir, shuffle, max_files)

    def _get_file_paths(
        self, directory: str, shuffle: bool, max_files: int
    ) -> List[str]:
        filenames = [
            name
            for name in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, name))
        ]

        if shuffle:
            random.shuffle(filenames)
        else:
            filenames.sort()

        if max_files is not None:
            filenames = filenames[:max_files]

        return [os.path.join(directory, name) for name in filenames]

    def for_each(self, f: Callable[[str], None]):
        for file_path in self.file_paths:
            f(file_path)

    def get_texts(self) -> List[str]:
        return [
            open(file_path, "r", encoding="utf-8").read()
            for file_path in self.file_paths
        ]
