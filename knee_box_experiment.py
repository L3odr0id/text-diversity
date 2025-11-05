import argparse
import tempfile
import os
import logging
from typing import List, Dict, Optional, Tuple
from concurrent.futures import as_completed
import multiprocessing
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch
from matplotlib.lines import Line2D


from keep_diverse import (
    LZMAAlgo,
    PoissonMetric,
    add_filter_args,
    TextsFilter,
    SplitSetsMark,
    FilteredFilesList,
    Knee,
    KneePlot,
    DisplayKneeArgs,
    save_plot_safely,
    safe_process_pool_executor,
)

from texts_diversity.files_list import FilesList
from tests_runner import TestsRunner, TestsRunnerFolder, TestsRunnerResult

from tests_runner import ErrorsCount

from src.args.runner_args import add_runner_args


def add_experiment_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--experiment-rounds",
        type=int,
        required=True,
    )


class CustomPlot(KneePlot):
    def __init__(self):
        pass

    # def __init__(self, output_file: str, display_knee_args: DisplayKneeArgs):
    #     super().__init__(output_file, display_knee_args)
    #     self.output_file = output_file
    #     self.display_knee_args = display_knee_args

    def draw(self, knee: Knee, round_number: int):
        pass


class CustomFilteredFilesList(FilteredFilesList):
    def __init__(self):
        self.list_to_save = []
        self.knee_point = 0
        self.counter = None

    def save(self, knee: Knee):
        self.knee_point = int(knee.value)
        self.list_to_save.extend(knee.good_files())
        self.counter = knee.counter


def _call_experiment(args, file_paths, i) -> Optional[Tuple[int, Counter, List[ErrorsCount], int]]:
    cff = CustomFilteredFilesList(
        # output_file_path=args.output_file_path,
    )

    TextsFilter(
        sets_split=SplitSetsMark(
            all_file_names=file_paths[: args.max_files],
            split_by=args.split_by,
            algo=LZMAAlgo(),
            metric=PoissonMetric(),
            relative_eps=args.relative_eps,
            max_tries=args.max_tries_per_filter_iteration,
            min_indices_count=args.min_indices_count,
            max_workers=args.max_workers,
        ),
        knee_plot=CustomPlot(
            # output_file=args.output_plot_path,
            # display_knee_args=DisplayKneeArgs(
            #     total_files_count=args.max_files,
            #     split_by=args.split_by,
            #     relative_eps=args.relative_eps,
            #     max_tries=args.max_tries_per_filter_iteration,
            #     min_indices_count=args.min_indices_count,
            #     filter_rounds=args.filter_rounds,
            # ),
        ),
        filtered_files_list=cff,
        max_iter=args.filter_rounds,
        max_workers=args.max_workers,
    ).process()

    temp_dir = tempfile.TemporaryDirectory()
    tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)

    errors_report_path = f"{i}_{args.errors_report}"

    tests_runner = TestsRunner(
        path_to_runner_main=args.runner_main,
        folder=tests_runner_folder,
        errors_report_file_path=errors_report_path,
        verilog_out_name=f"{i}_{args.verilog_out_name}",
        gh_pages_dir=args.gh_pages_dir,
    )

    logging.info("Getting filtered dataset errors...")

    filtered_file_count = len(cff.list_to_save)
    tests_runner_folder.copy_files(cff.list_to_save)
    runner_success = tests_runner.execute()

    if not runner_success:
        logging.error("Failed to get filtered errors. Test run failed or timed out.")
        return None

    result = TestsRunnerResult(errors_report_path)
    filtered_errors = result.read_result()
    logging.info(f"Found {len(filtered_errors)} unique error types in filtered dataset")

    return (cff.knee_point, cff.counter, filtered_errors, filtered_file_count)


def knee_plot(ax1, knee_points, marks_values):
    max_length = max(len(round_values) for round_values in marks_values)

    x_positions = []
    y_means = []
    y_mins = []
    y_maxs = []

    for x in range(max_length):
        y_values_at_x = []
        for round_values in marks_values:
            if x < len(round_values):
                y_values_at_x.append(round_values[x])

        if y_values_at_x:
            x_positions.append(x)
            y_means.append(np.mean(y_values_at_x))
            y_mins.append(np.min(y_values_at_x))
            y_maxs.append(np.max(y_values_at_x))

    ax1.fill_between(
        x_positions,
        y_mins,
        y_maxs,
        alpha=0.3,
        color="royalblue",
        label="Min/Max Range",
    )

    ax1.plot(
        x_positions,
        y_means,
        linewidth=4,
        color="royalblue",
        label="Mean",
        # marker="o",
        # markersize=4,
    )

    mean_knee = np.mean(knee_points)
    min_knee = np.min(knee_points)
    max_knee = np.max(knee_points)

    ax1.axvline(
        x=mean_knee,
        color="crimson",
        linestyle="--",
        linewidth=2,
        alpha=0.9,
        label=f"Mean knee: {mean_knee:.1f}",
    )

    ax1.axvspan(
        min_knee,
        max_knee,
        color="crimson",
        alpha=0.15,
    )

    ax1.set_xlabel("Files")
    ax1.set_ylabel("Times to remove")
    ax1.set_title("Range of times to remove vs knee point")
    ax1.grid(True, alpha=0.3)
    ax1.legend()


def box_plot(
    ax2,
    initial_errors_counts: List[ErrorsCount],
    filtered_errors_counts: List[ErrorsCount],
    initial_file_count: int,
    filtered_file_counts: List[int],
):
    logging.debug(f"box_plot: initial_errors_counts length: {len(initial_errors_counts)}")
    logging.debug(f"box_plot: filtered_errors_counts length: {len(filtered_errors_counts)}")
    logging.debug(f"box_plot: initial_file_count: {initial_file_count}")
    logging.debug(f"box_plot: filtered_file_counts: {filtered_file_counts}")

    initial_errors_data = {}

    for e in initial_errors_counts:
        initial_errors_data[e.error_id] = e.test_paths_count / initial_file_count

    all_error_ids = sorted(set(initial_errors_data.keys()))

    filtered_errors_data = {error_id: [] for error_id in all_error_ids}

    for errors_list, file_count in zip(filtered_errors_counts, filtered_file_counts):
        tmp_counter = Counter()
        for error_id in all_error_ids:
            tmp_counter[error_id] = 0
        for e in errors_list:
            tmp_counter[e.error_id] = e.test_paths_count / file_count

        for error_id in all_error_ids:
            filtered_errors_data[error_id].append(tmp_counter[error_id])

    if not all_error_ids:
        ax2.text(0.5, 0.5, "No errors found", ha="center", va="center")
        ax2.set_title("Tests with errors / total tests")
        return

    box_data = []
    initial_positions = []
    initial_values = []
    box_positions = []
    xticklabels = []

    for i, error_id in enumerate(all_error_ids):
        label = error_id[:20] + "..." if len(error_id) > 30 else error_id
        xticklabels.append(label)

        box_pos = i + 1
        box_positions.append(box_pos)
        box_data.append(filtered_errors_data[error_id])

        initial_positions.append(box_pos)
        initial_values.append(initial_errors_data.get(error_id, 0))

    bp = ax2.boxplot(box_data, positions=box_positions, widths=0.6, patch_artist=True)
    for b in bp["boxes"]:
        b.set_facecolor("orange")
        b.set_alpha(0.7)

    ax2.scatter(
        initial_positions,
        initial_values,
        color="lightblue",
        s=100,
        marker="o",
        zorder=3,
        label="Initial",
        edgecolors="darkblue",
        linewidths=1.5,
    )

    ax2.set_xticks(range(1, len(all_error_ids) + 1))
    ax2.set_xticklabels(xticklabels, rotation=45, ha="right")
    ax2.set_xlabel("Error Types")
    ax2.set_ylabel("Relative tests with errors")
    ax2.set_title("Initial vs Filtered: tests with errors / total tests")
    ax2.legend(
        handles=[
            Patch(facecolor="orange", alpha=0.7, label="Filtered"),
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                markerfacecolor="lightblue",
                markeredgecolor="darkblue",
                markersize=10,
                label="Initial",
            ),
        ],
        loc="upper right",
    )
    ax2.grid(True, alpha=0.3)


def produce_artifacts(
    output_plot_path,
    knee_points,
    marks_values,
    initial_errors_counts,
    filtered_errors_counts,
    initial_file_count,
    filtered_file_counts,
    title,
):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    knee_plot(ax1, knee_points, marks_values)
    box_plot(
        ax2,
        initial_errors_counts,
        filtered_errors_counts,
        initial_file_count,
        filtered_file_counts,
    )

    fig.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    save_plot_safely(fig, output_plot_path)
    logging.info(f"Visualization saved to {output_plot_path}")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--output-plot-path", type=str, required=True)
    parser.add_argument("--output-file-path", type=str, required=True)
    parser.add_argument("--dir", type=str, required=True)
    parser.add_argument("--max-files", type=int, required=True)


def main():
    logging.basicConfig(
        format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
        level=logging.INFO,
    )

    parser = argparse.ArgumentParser(description="")
    add_arguments(parser)
    add_filter_args(parser)
    add_experiment_args(parser)
    add_runner_args(parser)
    args = parser.parse_args()

    file_paths = [
        os.path.join(args.dir, name) for name in os.listdir(args.dir) if os.path.isfile(os.path.join(args.dir, name))
    ]

    artifacts_lock = multiprocessing.Lock()
    finished_rounds = 0

    knee_points = []
    marks_values = []  # List of lists: each inner list is sorted counter values from one round
    initial_errors_counts = []
    filtered_errors_counts = []
    filtered_file_counts = []
    initial_file_count = args.max_files

    temp_dir = tempfile.TemporaryDirectory()
    tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)

    files_list = FilesList(files_dir=args.dir, shuffle=False, max_files=args.max_files)
    tests_runner = TestsRunner(
        path_to_runner_main=args.runner_main,
        folder=tests_runner_folder,
        errors_report_file_path=f"initial_{args.errors_report}",
        verilog_out_name=f"initial_{args.verilog_out_name}",
        gh_pages_dir=args.gh_pages_dir,
    )
    logging.info("Getting initial dataset errors...")
    tests_runner_folder.copy_files(files_list.file_paths)
    tests_runner.execute()
    result = TestsRunnerResult(f"initial_{args.errors_report}")
    initial_errors_counts = result.read_result()
    logging.info(f"Found {len(initial_errors_counts)} unique error types in initial dataset")

    with safe_process_pool_executor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(_call_experiment, args, file_paths, i) for i in range(args.experiment_rounds)]

        for future in as_completed(futures):
            result = future.result()
            if result is None:
                continue
            knee_point, counter, errors_counts, filtered_file_count = result

            with artifacts_lock:
                finished_rounds += 1
                knee_points.append(knee_point)
                filtered_errors_counts.append(errors_counts)
                filtered_file_counts.append(filtered_file_count)
                marks_values.append(list(sorted(counter.values(), reverse=True)))
                produce_artifacts(
                    args.output_plot_path,
                    knee_points,
                    marks_values,
                    initial_errors_counts,
                    filtered_errors_counts,
                    initial_file_count,
                    filtered_file_counts,
                    f"Knee box experiment. Round {finished_rounds} / {args.experiment_rounds}. Files: {args.max_files}. Split by: {args.split_by}",
                )


if __name__ == "__main__":
    main()
