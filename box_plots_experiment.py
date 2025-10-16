import argparse
import math
import tempfile
import os
import random
import statistics
from typing import List, Tuple, Callable

from scipy.stats import poisson
from textdistance import EntropyNCD, LZMANCD
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from texts_diversity.common_distances import (
    always_0,
    always_1,
    LevenshteinDistanceNormalized,
)
from texts_diversity.files_list import FilesList
from texts_diversity.texts_diversity import TextsDiversity
from texts_diversity.plot_config import PlotConfig
from texts_diversity.metric import Metric
from texts_diversity.texts_distances import TextsDistances
from texts_diversity.algo import Algo
from texts_diversity.common_metrics import calc_mean_metric
from texts_diversity.common_normalization import min_max_normalization
from texts_diversity.plots_list import PlotsList
from min_distance_metric import MinDistanceMetric
from texts_diversity.calc_info import CalcInfo
from utils import cis_same_metric
from texts_diversity.iterative_plot_config import IterativePlotConfig
from texts_diversity.algo import CompressAlgo
from src.TDSM.TDS_metric import TDSMetric
from remove_percentage_compare_metric import RemovePercentageCompareFilter
from remove_percentage_compare_plot import RemovePercentageComparePlot
from src.TDSM.TDS_metric_plot import TDSMetricPlot
from tests_runner import TestsRunner, TestsRunnerFolder, TestsRunnerResult
from texts_diversity.utils import save_plot_safely
from src.pct_filter.filter_result import FilterResult
from src.metrics.poisson_dist_metric import poisson_dist_metric
from src.pct_filter.pct_filter import PctFilter

import logging

logging.basicConfig(
    format="%(asctime)s - %(relativeCreated)d ms - %(levelname)s - %(funcName)s - %(message)s",
    level=logging.DEBUG,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run box plots experiment with text corpus diversity filtering"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default="generated",
        help="Directory containing input files (default: generated)",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Shuffle files list (default: False)",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=200,
        help="Maximum number of files to process (default: 200)",
    )
    parser.add_argument(
        "--output-plot",
        type=str,
        default="test_box_plots.svg",
        help="Path for output plot file (default: test_box_plots.svg)",
    )
    parser.add_argument(
        "--runner-main",
        type=str,
        default="verilog-model/.github/workflows/runner/main.py",
        help="Path to runner main.py (default: verilog-model/.github/workflows/runner/main.py)",
    )
    parser.add_argument(
        "--errors-report",
        type=str,
        default="errors_report.json",
        help="Path to errors report JSON file (default: errors_report.json)",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=500,
        help="Number of iterations to run (default: 500)",
    )
    return parser.parse_args()


args = parse_args()

lzma_algo = Algo("LZMANCD", LZMANCD().distance, color="royalblue")
entropy_algo = Algo("EntropyNCD", EntropyNCD().distance, color="darkorange")

files_list = FilesList(dir=args.dir, shuffle=args.shuffle, max_files=args.max_files)

calc_infos = cis_same_metric(
    algos=[
        lzma_algo,
        entropy_algo,
    ],
    metric=poisson_dist_metric,
)

old_texts = []


def process_file(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        new_text = f.read()

    for calc_info in calc_infos:
        calc_info.distances.add_dist(old_texts, new_text)

    old_texts.append(new_text)


files_list.for_each(process_file)


def draw_boxplots(
    filter_results_dict,
    remaining_files_counts_dict,
    baseline_results_dict,
    eps_values,
    calc_infos_list,
    iteration_num,
    total_files_count,
    output_plot_path,
):
    logging.info(f"\nDrawing boxplots for iteration {iteration_num}...")

    label_to_algo = {}
    for calc_info in calc_infos_list:
        label = calc_info.label()
        label_to_algo[label] = {
            "color": calc_info.distances.algo.color,
            "name": calc_info.distances.algo.name,
        }

    baseline_color = "lightgray"
    baseline_label = "Unfiltered"

    fig, axes = plt.subplots(
        nrows=len(eps_values),
        ncols=2,
        figsize=(24, 6 * len(eps_values)),
    )

    if len(eps_values) == 1:
        axes = [axes]

    metrics_to_plot = ["overall", "test_paths_count"]
    metric_titles = ["Overall errors", "Tests with errors"]

    for idx, eps in enumerate(eps_values):
        for metric_idx, (metric_key, metric_title) in enumerate(
            zip(metrics_to_plot, metric_titles)
        ):
            ax = axes[idx][metric_idx]

            error_ids = sorted(filter_results_dict[eps].keys())

            if not error_ids:
                ax.text(0.5, 0.5, "No errors found", ha="center", va="center")
                ax.set_title(
                    f"{metric_title} - relative_eps = {eps} (iteration {iteration_num})"
                )
                continue

            all_data = []
            positions = []
            labels_for_x = []
            box_colors = []
            unique_labels = set()
            has_baseline = False

            for i, error_id in enumerate(error_ids):
                num_boxes_for_this_error = 0
                base_pos = (
                    i * 4
                )  # Space out error groups (4 to accommodate 3 boxes + gap)

                if error_id in baseline_results_dict:
                    baseline_counts = baseline_results_dict[error_id][metric_key][
                        :iteration_num
                    ]
                    if baseline_counts:
                        normalized_baseline = [
                            count / total_files_count for count in baseline_counts
                        ]
                        all_data.append(normalized_baseline)
                        box_colors.append(baseline_color)
                        positions.append(base_pos + num_boxes_for_this_error)
                        num_boxes_for_this_error += 1
                        has_baseline = True

                labels_for_this_error = sorted(
                    filter_results_dict[eps][error_id].keys()
                )

                for label in labels_for_this_error:
                    normalized_counts = []
                    for iter_idx, item in enumerate(
                        filter_results_dict[eps][error_id][label]
                    ):
                        file_count = remaining_files_counts_dict[eps][label][iter_idx]
                        normalized_count = (
                            item[metric_key] / file_count if file_count > 0 else 0
                        )
                        normalized_counts.append(normalized_count)

                    all_data.append(normalized_counts)

                    if label in label_to_algo:
                        box_colors.append(label_to_algo[label]["color"])
                        unique_labels.add(label)

                    positions.append(base_pos + num_boxes_for_this_error)
                    num_boxes_for_this_error += 1

                labels_for_x.append(error_id[:30] if len(error_id) > 30 else error_id)

            bp = ax.boxplot(
                all_data,
                positions=positions,
                widths=0.6,
                patch_artist=True,
            )

            for patch_idx, patch in enumerate(bp["boxes"]):
                patch.set_facecolor(box_colors[patch_idx])
                patch.set_alpha(0.7)

            x_tick_positions = [i * 4 + 1 for i in range(len(error_ids))]
            ax.set_xticks(x_tick_positions)
            ax.set_xticklabels(labels_for_x, rotation=45, ha="right")

            ax.set_ylabel("%")
            ax.set_xlabel("Error ID")

            title = f"{metric_title} / filtered files count (relative_eps = {eps}, iteration {iteration_num})"
            if eps in remaining_files_counts_dict and remaining_files_counts_dict[eps]:
                median_info = []
                for label in sorted(remaining_files_counts_dict[eps].keys()):
                    counts = remaining_files_counts_dict[eps][label][:iteration_num]
                    if counts:
                        median_count = statistics.median(counts)
                        algo_name = (
                            label_to_algo[label]["name"]
                            if label in label_to_algo
                            else label
                        )
                        median_info.append(f"{algo_name}: {median_count:.0f} files")
                if median_info:
                    title += f"\nMedian remaining: {', '.join(median_info)}"

            ax.set_title(title)
            ax.grid(True, alpha=0.3)

            legend_elements = []

            if has_baseline:
                legend_elements.append(
                    Patch(facecolor=baseline_color, alpha=0.7, label=baseline_label)
                )

            for label in sorted(unique_labels):
                if label in label_to_algo:
                    legend_elements.append(
                        Patch(
                            facecolor=label_to_algo[label]["color"],
                            alpha=0.7,
                            label=label_to_algo[label]["name"],
                        )
                    )
            if legend_elements:
                ax.legend(handles=legend_elements, loc="upper right")

    plt.tight_layout()
    save_plot_safely(fig, output_plot_path)
    logging.info(f"Boxplot saved for iteration {iteration_num}")


temp_dir = tempfile.TemporaryDirectory()

tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)
tests_runner = TestsRunner(
    path_to_runner_main=args.runner_main,
    folder=tests_runner_folder,
    errors_report_file_path=args.errors_report,
)

filter_results = {}  # Organized by eps -> error_id -> label -> list of measurements
remaining_files_counts = {}  # Organized by eps -> label -> list of counts
baseline_results = (
    {}
)  # Initial unfiltered error counts: error_id -> {"overall": list, "test_paths_count": list}

initial_indices = list(range(len(files_list.file_paths)))
relative_eps_to_test = [0.00001]
max_tries = 10
min_indices_count = 10


for eps in relative_eps_to_test:
    filter_results[eps] = {}
    remaining_files_counts[eps] = {}

for i in range(args.iterations):
    logging.info(f"\n{'='*60}")
    logging.info(f"=== Iteration {i + 1} ===")
    logging.info(f"{'='*60}")

    logging.info("\nCollecting baseline (unfiltered) error counts...")
    baseline_file_paths = files_list.file_paths
    tests_runner_folder.copy_files(baseline_file_paths)
    baseline_success = tests_runner.execute()

    if not baseline_success:
        logging.info(
            "WARNING: Baseline test run failed or timed out. Skipping baseline for this iteration."
        )
    else:
        baseline_result = TestsRunnerResult(args.errors_report)
        baseline_errors = baseline_result.read_result()

        for error_count in baseline_errors:
            error_id = error_count.error_id
            if error_id not in baseline_results:
                baseline_results[error_id] = {"overall": [], "test_paths_count": []}
            baseline_results[error_id]["overall"].append(error_count.overall)
            baseline_results[error_id]["test_paths_count"].append(
                error_count.test_paths_count
            )

        logging.info(f"Baseline: Found {len(baseline_errors)} unique error types")

    for eps in relative_eps_to_test:
        logging.info(f"\nTesting with relative_eps = {eps}")

        for calc_info in calc_infos:
            logging.info(f"\nProcessing {calc_info.label()}")

            initial_metric_value = calc_info.metric.calc(calc_info.distances)
            logging.info(f"Initial metric value: {initial_metric_value}")

            pct_filter = PctFilter(
                initial_indices=initial_indices,
                relative_eps=eps,
                max_tries=max_tries,
                intial_metric_value=initial_metric_value,
                min_indices_count=min_indices_count,
                calc_info=calc_info,
            )

            while not pct_filter.is_finished:
                pct_filter.iterate()

            remaining_file_paths = [
                files_list.file_paths[idx] for idx in pct_filter.current_idxs
            ]
            logging.info(f"Files remaining after filter: {len(remaining_file_paths)}")

            label = calc_info.label()
            if label not in remaining_files_counts[eps]:
                remaining_files_counts[eps][label] = []
            remaining_files_counts[eps][label].append(len(remaining_file_paths))

            tests_runner_folder.copy_files(remaining_file_paths)

            logging.info("Running tests...")
            runner_success = tests_runner.execute()

            if not runner_success:
                logging.info(
                    f"WARNING: Filtered test run failed or timed out for {label}. Skipping this iteration."
                )
            else:
                result = TestsRunnerResult(args.errors_report)
                errors_counts = result.read_result()

                for error_count in errors_counts:
                    error_id = error_count.error_id
                    if error_id not in filter_results[eps]:
                        filter_results[eps][error_id] = {}

                    if label not in filter_results[eps][error_id]:
                        filter_results[eps][error_id][label] = []

                    filter_results[eps][error_id][label].append(
                        {
                            "iteration": i,
                            "overall": error_count.overall,
                            "test_paths_count": error_count.test_paths_count,
                        }
                    )

                logging.info(f"Found {len(errors_counts)} unique error types")

    draw_boxplots(
        filter_results,
        remaining_files_counts,
        baseline_results,
        relative_eps_to_test,
        calc_infos,
        i + 1,
        len(files_list.file_paths),
        args.output_plot,
    )

logging.info(f"\n{'='*60}")
logging.info(f"=== Final Summary ===")
logging.info(f"{'='*60}")

for eps in relative_eps_to_test:
    logging.info(f"\n--- Results for relative_eps = {eps} ---")
    logging.info(f"Collected results for {len(filter_results[eps])} error types")

    logging.info(f"\nMedian Remaining Files:")
    for label, counts in remaining_files_counts[eps].items():
        median_count = statistics.median(counts)
        logging.info(f"  {label}: {median_count} (from {counts})")
