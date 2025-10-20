import logging
import argparse
from errors_for_given_files import errors_for_given_paths
from texts_diversity.files_list import FilesList

logging.basicConfig(
    format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
    level=logging.DEBUG,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run box plots experiment with text corpus diversity filtering"
    )
    parser.add_argument(
        "--file-with-paths",
        type=str,
        default="generated",
    )
    parser.add_argument(
        "--max-files",
        type=int,
    )
    parser.add_argument(
        "--path-to-runner-main",
        type=str,
    )
    parser.add_argument(
        "--errors-report-file-path",
        type=str,
    )
    return parser.parse_args()


args = parse_args()

file_paths = []
with open(args.file_with_paths, "r") as file:
    file_paths = file.readlines()

file_paths = [f.rstrip("\n") for f in file_paths]

logging.debug(f"Got {len(file_paths)} files")
file_paths = file_paths[: args.max_files]

logging.debug(f"{len(file_paths)} files after cut")

errors_for_given_paths(
    file_paths=file_paths,
    path_to_runner_main=args.path_to_runner_main,
    errors_report_file_path=args.errors_report_file_path,
)
