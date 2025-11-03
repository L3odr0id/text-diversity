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


def _call_experiment(
    args, file_paths, i
) -> Optional[Tuple[int, Counter, List[ErrorsCount], int]]:
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

    ax1.axvline(
        x=mean_knee,
        color="crimson",
        linestyle="--",
        linewidth=2,
        alpha=0.9,
        label=f"Knee point: {mean_knee:.1f}",
    )

    knee_span = 0.5  # Half-width of the span
    ax1.axvspan(
        mean_knee - knee_span,
        mean_knee + knee_span,
        color="crimson",
        alpha=0.15,
    )

    ax1.set_xlabel("Files count")
    ax1.set_ylabel("Times to remove")
    ax1.set_title("Range of times to remove vs knee point")
    ax1.grid(True, alpha=0.3)
    ax1.legend()


def box_plot(
    ax2,
    initial_errors_counts,
    filtered_errors_counts,
    initial_file_count,
    filtered_file_counts,
):
    initial_error_dict = {
        e.error_id: e.test_paths_count for e in (initial_errors_counts or [])
    }

    filtered_error_values = {}
    for round_idx, errors_counts in enumerate(filtered_errors_counts or []):
        file_count = (
            filtered_file_counts[round_idx]
            if round_idx < len(filtered_file_counts)
            else 0
        )
        if file_count <= 0:
            continue
        for e in errors_counts:
            normalized_value = e.test_paths_count / file_count if file_count > 0 else 0
            filtered_error_values.setdefault(e.error_id, []).append(normalized_value)

    all_error_ids = sorted(
        set(initial_error_dict.keys()) | set(filtered_error_values.keys())
    )

    if not all_error_ids:
        ax2.text(0.5, 0.5, "No errors found", ha="center", va="center")
        ax2.set_title("Tests with errors / total tests")
        return

    all_data = []
    positions = []
    box_colors = []
    xticklabels = []

    for i, err_id in enumerate(all_error_ids):
        base = i * 3
        xticklabels.append(err_id[:30] + "..." if len(err_id) > 30 else err_id)

        if (
            initial_file_count
            and initial_file_count > 0
            and err_id in initial_error_dict
        ):
            normalized_initial = initial_error_dict[err_id] / initial_file_count
            all_data.append([normalized_initial])
        else:
            all_data.append([])
        positions.append(base + 0)
        box_colors.append("lightblue")

        filtered_values = filtered_error_values.get(err_id, [])
        all_data.append(filtered_values)
        positions.append(base + 1)
        box_colors.append("orange")

    plot_data = []
    plot_pos = []
    plot_colors = []
    for d, p, c in zip(all_data, positions, box_colors):
        if d is not None and len(d) > 0:
            plot_data.append(d)
            plot_pos.append(p)
            plot_colors.append(c)

    if plot_data:
        bp = ax2.boxplot(plot_data, positions=plot_pos, widths=0.6, patch_artist=True)
        for i, b in enumerate(bp["boxes"]):
            b.set_facecolor(plot_colors[i])
            b.set_alpha(0.7)

    if all_error_ids:
        ax2.set_xticks([i * 3 + 0.5 for i in range(len(all_error_ids))])
        ax2.set_xticklabels(xticklabels, rotation=45, ha="right")

    ax2.set_xlabel("Error Types")
    ax2.set_ylabel("Relative tests with errors")
    ax2.set_title("Initial vs Filtered: tests with errors / total tests")
    ax2.legend(
        handles=[
            Patch(facecolor="lightblue", alpha=0.7, label="Initial"),
            Patch(facecolor="orange", alpha=0.7, label="Filtered"),
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
        os.path.join(args.dir, name)
        for name in os.listdir(args.dir)
        if os.path.isfile(os.path.join(args.dir, name))
    ]

    artifacts_lock = multiprocessing.Lock()
    finished_rounds = 0

    knee_points = []
    marks_values = (
        []
    )  # List of lists: each inner list is sorted counter values from one round
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
    logging.info(
        f"Found {len(initial_errors_counts)} unique error types in initial dataset"
    )

    with safe_process_pool_executor(max_workers=args.max_workers) as executor:
        futures = [
            executor.submit(_call_experiment, args, file_paths, i)
            for i in range(args.experiment_rounds)
        ]

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
                )


if __name__ == "__main__":
    main()
