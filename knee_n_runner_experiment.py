import argparse
import tempfile
import os
import logging
from typing import List, Dict

import matplotlib.pyplot as plt
import numpy as np

from src.knee.knee import Knee
from texts_diversity.files_list import FilesList
from tests_runner import TestsRunner, TestsRunnerFolder, TestsRunnerResult
from src.knee.knee_cut import KneeCut
from src.basic.counter_report import CounterReport
from texts_diversity.utils import save_plot_safely

logging.basicConfig(
    format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
    level=logging.DEBUG,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Run knee & runner experiment")
    parser.add_argument(
        "--dir",
        type=str,
        default="generated",
        help="Directory containing input files (default: generated)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum number of files to process (default: 200)",
    )
    parser.add_argument(
        "--runner-main",
        type=str,
        default="verilog-model/.github/workflows/runner/tools-run/main.py",
        help="Path to runner main.py (default: verilog-model/.github/workflows/runner/tools-run/main.py)",
    )
    parser.add_argument(
        "--errors-report",
        type=str,
        default="errors_report.json",
        help="Path to errors report JSON file (default: errors_report.json)",
    )
    parser.add_argument(
        "--counter-results",
        type=str,
        required=True,
        help="Path to counter results JSON file",
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default="knee_runner_experiment.svg",
        help="Path for output plot file (default: knee_runner_experiment.svg)",
    )
    parser.add_argument(
        "--knee-plot-path",
        type=str,
        default="knee_plot.svg",
        help="Path for knee plot file (default: knee_plot.svg)",
    )
    parser.add_argument(
        "--cut-result-file",
        type=str,
        default="cut_result.txt",
        help="Path for cut result file (default: cut_result.txt)",
    )
    return parser.parse_args()


def get_initial_errors(
    files_list: FilesList,
    tests_runner: TestsRunner,
    tests_runner_folder: TestsRunnerFolder,
) -> List:
    logging.info("Getting initial dataset errors...")

    tests_runner_folder.copy_files(files_list.file_paths)
    runner_success = tests_runner.execute()

    if not runner_success:
        logging.error("Failed to get initial errors. Test run failed or timed out.")
        return []

    result = TestsRunnerResult(args.errors_report)
    initial_errors = result.read_result()
    logging.info(f"Found {len(initial_errors)} unique error types in initial dataset")

    return initial_errors


def apply_knee_cut_and_get_filtered_files(
    counter_results_path: str, files_list: FilesList
) -> List[str]:
    logging.info("Applying knee cut...")

    knee_cut = KneeCut(
        knee_plot_path=args.knee_plot_path,
        counter_report_file=counter_results_path,
        cut_result_file=args.cut_result_file,
    )

    knee_cut.cut()

    with open(args.cut_result_file, "r") as f:
        filtered_file_names = [line.strip() for line in f.readlines()]

    filtered_file_paths = []
    for file_name in filtered_file_names:
        filtered_file_paths.append(file_name)

    logging.info(
        f"Knee cut resulted in {len(filtered_file_paths)} files (from {len(files_list.file_paths)} total)"
    )

    return filtered_file_paths


def get_filtered_errors(
    filtered_file_paths: List[str],
    tests_runner: TestsRunner,
    tests_runner_folder: TestsRunnerFolder,
) -> List:
    logging.info("Getting filtered dataset errors...")

    tests_runner_folder.copy_files(filtered_file_paths)
    runner_success = tests_runner.execute()

    if not runner_success:
        logging.error("Failed to get filtered errors. Test run failed or timed out.")
        return []

    result = TestsRunnerResult(args.errors_report)
    filtered_errors = result.read_result()
    logging.info(f"Found {len(filtered_errors)} unique error types in filtered dataset")

    return filtered_errors


def create_visualization(
    initial_errors: List,
    filtered_errors: List,
    initial_file_count: int,
    filtered_file_count: int,
):
    logging.info("Creating visualization...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    counter_report = CounterReport(args.counter_results)
    counter_report.load_counter()

    sorted_items = sorted(
        counter_report.counter.items(), key=lambda x: x[1], reverse=True
    )
    file_names, y_values = zip(*sorted_items)
    x_values = list(range(len(y_values)))

    knee = Knee(x_values=x_values, y_values=y_values)
    knee.draw(ax=ax1)

    initial_error_dict = {error.error_id: error.overall for error in initial_errors}
    filtered_error_dict = {error.error_id: error.overall for error in filtered_errors}

    all_error_ids = set(initial_error_dict.keys()) | set(filtered_error_dict.keys())

    initial_rates = []
    filtered_rates = []
    error_labels = []

    for error_id in sorted(all_error_ids):
        initial_count = initial_error_dict.get(error_id, 0)
        filtered_count = filtered_error_dict.get(error_id, 0)

        initial_rate = (
            initial_count / initial_file_count if initial_file_count > 0 else 0
        )
        filtered_rate = (
            filtered_count / filtered_file_count if filtered_file_count > 0 else 0
        )

        initial_rates.append(initial_rate)
        filtered_rates.append(filtered_rate)
        error_labels.append(error_id[:20] + "..." if len(error_id) > 20 else error_id)

    x = np.arange(len(error_labels))
    width = 0.35

    bars1 = ax2.bar(
        x - width / 2,
        initial_rates,
        width,
        label=f"Initial ({initial_file_count} files)",
        alpha=0.7,
        color="lightblue",
    )
    bars2 = ax2.bar(
        x + width / 2,
        filtered_rates,
        width,
        label=f"Filtered ({filtered_file_count} files)",
        alpha=0.7,
        color="orange",
    )

    for i, (bar1, bar2) in enumerate(zip(bars1, bars2)):
        error_id = sorted(all_error_ids)[i]
        initial_count = initial_error_dict.get(error_id, 0)
        filtered_count = filtered_error_dict.get(error_id, 0)

        if bar1.get_height() > 0:
            ax2.text(
                bar1.get_x() + bar1.get_width() / 2,
                bar1.get_height() + 0.001,
                str(initial_count),
                ha="center",
                va="bottom",
                fontsize=8,
            )

        if bar2.get_height() > 0:
            ax2.text(
                bar2.get_x() + bar2.get_width() / 2,
                bar2.get_height() + 0.001,
                str(filtered_count),
                ha="center",
                va="bottom",
                fontsize=8,
            )

    ax2.set_xlabel("Error Types")
    ax2.set_ylabel("Error Rate (errors per file)")
    ax2.set_title("Error Rates: Initial vs Filtered Dataset")
    ax2.set_xticks(x)
    ax2.set_xticklabels(error_labels, rotation=45, ha="right")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    save_plot_safely(fig, args.output_plot)
    logging.info(f"Visualization saved to {args.output_plot}")


def main():
    global args
    args = parse_args()

    logging.info(f"Starting knee & runner experiment")
    logging.info(f"Directory: {args.dir}")
    logging.info(f"Max files: {args.max_files}")
    logging.info(f"Counter results: {args.counter_results}")

    files_list = FilesList(files_dir=args.dir, shuffle=False, max_files=args.max_files)
    logging.info(f"Loaded {len(files_list.file_paths)} files")

    temp_dir = tempfile.TemporaryDirectory()
    tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)
    tests_runner = TestsRunner(
        path_to_runner_main=args.runner_main,
        folder=tests_runner_folder,
        errors_report_file_path=args.errors_report,
    )

    initial_errors = get_initial_errors(files_list, tests_runner, tests_runner_folder)
    if not initial_errors:
        logging.error("Failed to get initial errors. Exiting.")
        return

    filtered_file_paths = apply_knee_cut_and_get_filtered_files(
        args.counter_results, files_list
    )
    if not filtered_file_paths:
        logging.error("Failed to get filtered files. Exiting.")
        return

    filtered_errors = get_filtered_errors(
        filtered_file_paths, tests_runner, tests_runner_folder
    )
    if not filtered_errors:
        logging.error("Failed to get filtered errors. Exiting.")
        return

    create_visualization(
        initial_errors,
        filtered_errors,
        len(files_list.file_paths),
        len(filtered_file_paths),
    )

    logging.info("Knee & runner experiment completed successfully!")


if __name__ == "__main__":
    main()
