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
        gh_pages_dir: str,
        verilog_out_name: str = "a.out",
    ):
        self.verilog_out_name = verilog_out_name
        self.command = (
            f"""
python3 {path_to_runner_main} \
    --gen-path """
            + f'"{folder.path}"'
            + r""" --job-link "https://github.com/DepTyCheck/verilog-model/" --tool-name "iverilog" --tool-error-regex "(syntax error\W[A-z-\/0-9,.:]+ .*$|(error|sorry|assert|vvp): [\S ]+$)" --error-distances-output "error_distances.html" --extra-ignored-regexes "Unable to elaborate r-value: ['{}d0-9]+" --run-statistics-output """
            + f'"{errors_report_file_path}" --commit "does_not_matter"'
            + f" --ignored-errors-dir {gh_pages_dir}"
            + f' --tool-cmd "iverilog -g2012 -o {self.verilog_out_name}'
            + ' {file}"'
        )

    def execute(self):
        print("Running command: ", self.command)
        try:
            result = subprocess.run(
                self.command,
                shell=True,
                # stdout=subprocess.DEVNULL,
                # stderr=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=500,
            )
            # print(f"out")
            # print(result.stdout)
            print("err")
            print(result.stderr)
            print(f"Test runner completed.")
        except subprocess.TimeoutExpired:
            print(f"WARNING: Test runner timed out after 300 seconds!")
            return False
        except Exception as e:
            print(f"ERROR: Test runner failed with exception: {e}")
            return False

        try:
            os.remove(self.verilog_out_name)
            print(f"Removed {self.verilog_out_name} from current directory.")
        except Exception as e:
            print(f"Failed to remove {self.verilog_out_name}: {e}")

        return True


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
