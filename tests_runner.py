import subprocess
from dataclasses import dataclass
from typing import List
import json


class TestsRunner:
    def __init__(self, command: str):
        self.command = command

    def execute(self):
        subprocess.run(self.command, shell=True)


@dataclass
class ErrorsCount:
    overall: int
    tests_paths: List[str]
    error_id: str


class TestsRunnerResult:
    def __init__(self, output_path: str):
        self.output_path = output_path

    def read_result(self) -> List[ErrorsCount]:
        with open(self.output_path, "r") as f:
            data = json.load(f)
            errors = data.get("errors", [])
            return [ErrorsCount(**error_count) for error_count in errors]
