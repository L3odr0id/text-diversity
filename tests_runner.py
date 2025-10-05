import subprocess
from dataclasses import dataclass
from typing import List
import json
import os
import shutil


class TestsRunnerFolder:
    def __init__(self, path: str):
        self.path = path

    def setup(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def clear(self):
        self.setup()
        for filename in os.listdir(self.path):
            file_path = os.path.join(self.path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

    def copy_files(self, file_paths: List[str]):
        self.clear()

        for file_path in file_paths:
            original_file_path = file_path
            filename = os.path.basename(original_file_path)
            dest_path = os.path.join(self.path, filename)
            shutil.copy2(original_file_path, dest_path)

        print(f"Copied {len(file_paths)} files to {self.path}")


class TestsRunner:
    def __init__(
        self,
        path_to_runner_main: str,
        folder: TestsRunnerFolder,
        errors_report_file_path: str,
    ):
        self.command = (
            f"""
python3 {path_to_runner_main} \
    --gen-path """
            + f'"{folder.path}"'
            + """ \
    --job-link "https://github.com/DepTyCheck/verilog-model/" \
    --tool-cmd "iverilog -g2012 -o a.out {file}" \
    --tool-name "iverilog" \
    --tool-error-regex "(syntax error\W[A-z-\/0-9,.:]+ .*$|(error|sorry|assert|vvp): [\S ]+$)" \
    --sim-cmd "vvp a.out" \
    --sim-error-regex "(syntax error\W[A-z-\/0-9,.:]+ .*$|(error|sorry|assert|vvp): [\S ]+$)" \
    --ignored-errors-dir "verilog-gh-pages/found_errors/iverilog" \
    --error-distances-output "error_distances.html" \
    --extra-ignored-regexes "Unable to elaborate r-value: ['{}d0-9]+" \
    --known-errors-report-output """
            + f'"{errors_report_file_path}"'
        )

    def execute(self):
        subprocess.run(self.command, shell=True)


@dataclass
class ErrorsCount:
    overall: int
    tests_paths: List[str]
    test_paths_count: int
    error_id: str


class TestsRunnerResult:
    def __init__(self, errors_report_file_path: str):
        self.errors_report_file_path = errors_report_file_path

    def read_result(self) -> List[ErrorsCount]:
        with open(self.errors_report_file_path, "r") as f:
            data = json.load(f)
            errors = data.get("errors", [])
            return [ErrorsCount(**error_count) for error_count in errors]
