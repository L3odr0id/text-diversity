import tempfile
import logging
from functools import cmp_to_key

from tests_runner import TestsRunner, TestsRunnerFolder, TestsRunnerResult


def errors_for_given_paths(file_paths, path_to_runner_main, errors_report_file_path):
    temp_dir = tempfile.TemporaryDirectory()

    tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)
    tests_runner_folder.copy_files(file_paths)
    tests_runner = TestsRunner(
        path_to_runner_main=path_to_runner_main,
        folder=tests_runner_folder,
        errors_report_file_path=errors_report_file_path,
    )

    runner_success = tests_runner.execute()

    if not runner_success:
        logging.info(f"WARNING: Filtered test run failed or timed out for")
    else:
        result = TestsRunnerResult(errors_report_file_path)
        errors_counts = result.read_result()

        sorted(errors_counts, key=lambda item: item.error_id)

        print("{:<80} {:<10} {:<12}".format("Error ID", "Overall", "Test Files"))
        print("-" * (80 + 10 + 12 + 2))

        for er in errors_counts:
            print(
                "{:<80} {:<10} {:<12}".format(
                    er.error_id, er.overall, er.test_paths_count
                )
            )
