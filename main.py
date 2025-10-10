import argparse
import math
import tempfile
import os
import random
from typing import List, Tuple, Callable

from scipy.stats import poisson
from textdistance import EntropyNCD, LZMANCD
import matplotlib.pyplot as plt

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
from tests_runner import TestsRunner, TestsRunnerFolder
from texts_diversity.utils import save_plot_safely
from src.pct_filter.filter_result import FilterResult


# def calc_novelty_metric(distances: Distances) -> float:
#     return distances.min_distance_from_last() or 0.0


# def calc_sqrt_sum_squared_metric(distances: Distances) -> float:
#     try:
#         center_idx, _, _ = distances.find_minimax_center()
#         return calc_custom_metric(distances, center_idx)
#     except (ValueError, Exception):
#         return float("nan")


# def calc_custom_metric(distances: Distances, center_idx: int) -> float:
#     num_texts = distances.maxKey() + 1
#     if num_texts < 2:
#         return float("nan")

#     dists = []
#     for i in range(num_texts):
#         if i != center_idx:
#             d = distances.distance(center_idx, i)
#             dists.append(d)

#     sum_sq = sum(d * d for d in dists)
#     mean_sq = sum_sq / (len(dists) / 2) if dists else 0.0

#     return mean_sq


def custom_entropy(a: str, b: str):
    return EntropyNCD().distance(a, b) * 5


# def calc_mean_sqrt_sum_squared_metric(distances: Distances) -> float:
#     distance_values = distances.get_values()
#     sum_squared = sum(distance * distance for distance in distance_values)
#     mean_sum_squared = sum_squared / len(distance_values)
#     return math.sqrt(mean_sum_squared)


def calc_mean_sqrt_sum_squared_metric_from_minimax_center(
    distances: TextsDistances,
) -> float:
    center_idx, _, _ = distances.find_minimax_center()
    num_texts = distances.max_key() + 1
    if num_texts < 2:
        return float("nan")

    distances_from_center = []
    for i in range(num_texts):
        if i != center_idx:
            distance = distances.distance(center_idx, i)
            distances_from_center.append(distance)

    sum_squared = sum(distance * distance for distance in distances_from_center)
    mean_sum_squared = sum_squared / len(distances_from_center)
    return math.sqrt(mean_sum_squared)


def calc_poisson_distribution(distances: TextsDistances) -> float:
    distance_values = distances.get_normalized_values()
    distance_values.sort()
    values = []
    for i in range(len(distance_values)):
        value = 2 * distance_values[i] * poisson.pmf(i, len(distance_values))
        values.append(value)
    return sum(values)


def calc_poisson_mins(distances: TextsDistances) -> float:
    """Calculate Poisson distribution using minimal distances for each text."""
    num_texts = distances.max_key() + 1
    min_distances = []

    for i in range(num_texts):
        distances_to_others = [
            distances.distance(i, j)
            for j in range(num_texts)
            if i != j and not math.isnan(distances.distance(i, j))
        ]
        min_distances.append(min(distances_to_others))

    if not min_distances:
        return float("nan")

    if distances.normalize:
        min_distances = distances.normalize(min_distances)

    min_distances.sort()
    values = []
    for i in range(len(min_distances)):
        value = 2 * min_distances[i] * poisson.pmf(i, len(min_distances))
        values.append(value)
    return sum(values)


# def calc_poisson_distribution_plus_1_minus_always_1(distances: Distances) -> float:
#     poisson_value = calc_poisson_distribution(distances=distances)
#     always_1_dist = Distances(distance_func=always_1, algo_name="Always 1")
#     always_1_dist._data = {(i, j): 1 for (i, j) in distances._data}
#     always_1_poisson = calc_poisson_distribution(distances=always_1_dist)
#     return poisson_value + 1 - always_1_poisson


def lzma_compress(text: str) -> bytes:
    return LZMANCD()._compress(bytes(text, "utf-8"))


lzma_algo_compress = CompressAlgo(name="LZMA", func=lzma_compress, color="royalblue")


def entropy_compress(text: str) -> bytes:
    return EntropyNCD()._compress(bytes(text, "utf-8"))


entropy_algo_compress = CompressAlgo(
    name="Entropy", func=entropy_compress, color="darkorange"
)

lzma_algo = Algo("LZMANCD", LZMANCD().distance, color="royalblue")
entropy_algo = Algo("EntropyNCD", EntropyNCD().distance, color="darkorange")
entropy_algo_x5 = Algo("EntropyNCD * 5", custom_entropy, color="chocolate")
poisson_metric = Metric("Poisson_dist", calc_poisson_distribution)
poisson_mins_metric = Metric("Poisson_mins", calc_poisson_mins)


def poisson_dist_metric():
    return Metric(name="Poisson_dist", calc=calc_poisson_distribution)


def main() -> None:
    parser = argparse.ArgumentParser(description="Text sets diversity utility")
    parser.add_argument("directory", help="Path to directory containing text files")
    parser.add_argument(
        "--max-files", type=int, help="Maximum number of files to analyze"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Name of the output plot file",
        default="ncd_stats_plots.png",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Randomly shuffle filenames instead of sorting them",
    )
    parser.add_argument(
        "--runner-main-path",
        type=str,
    )
    parser.add_argument(
        "--errors-report-file-path",
        type=str,
        help="Path to the output of the test runner",
    )
    parser.add_argument(
        "--relative-eps",
        type=float,
        default=0.001,
        help="Relative epsilon for filter (default: 0.001)",
    )
    parser.add_argument(
        "--max-tries",
        type=int,
        default=10,
        help="Maximum number of tries for each filter attempt (default: 10)",
    )
    parser.add_argument(
        "--report-pattern",
        type=str,
        required=True,
        help="Report pattern for filter results",
    )
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files
    output_file = args.output
    shuffle = args.shuffle
    path_to_runner_main = args.runner_main_path
    errors_report_file_path = args.errors_report_file_path
    relative_eps = args.relative_eps
    max_tries = args.max_tries
    report_pattern = args.report_pattern

    files_list = FilesList(dir=directory, shuffle=shuffle, max_files=max_files)

    calc_infos_list = [
        CalcInfo(metric=poisson_dist_metric(), algo=lzma_algo),
        CalcInfo(metric=poisson_dist_metric(), algo=entropy_algo),
    ]

    total_rows = 4
    total_cols = 16

    fig, axes = plt.subplots(
        total_rows,
        total_cols,
        figsize=(10 * total_cols, 6 * total_rows),
    )
    fig.tight_layout(w_pad=8, h_pad=5, rect=[0.05, 0.05, 0.95, 0.95])
    fig.suptitle("Iterative tests set analysis", fontsize=16)

    axes_flat = axes.flatten()

    plot_configs = []

    for i, calc_info in enumerate(calc_infos_list):
        row_start_idx = i * total_cols
        plot_configs.append(
            PlotConfig(
                name=f"{calc_info.distances.algo.name} - Poisson distance vs number of files",
                calc_infos=[calc_info],
                axes=[axes_flat[row_start_idx]],
            )
        )

    temp_dir = tempfile.TemporaryDirectory()

    tests_runner_folder = TestsRunnerFolder(path=temp_dir.name)
    tests_runner = TestsRunner(
        path_to_runner_main=path_to_runner_main,
        folder=tests_runner_folder,
        errors_report_file_path=errors_report_file_path,
    )

    TextsDiversity(
        min_files_for_analysis=10,
        files_list=files_list,
        plots_list=PlotsList(
            configs=plot_configs,
            output_file=output_file,
            fig=fig,
        ),
    ).draw_plots()

    pct_filters: List[RemovePercentageCompareFilter] = []
    compare_calc_infos_list = list(reversed(calc_infos_list))

    for i in range(len(calc_infos_list)):
        main_calc_info = calc_infos_list[i]
        compare_calc_info = compare_calc_infos_list[i]

        pct_filter = RemovePercentageCompareFilter(
            main_calc_info=main_calc_info,
            compare_calc_info=compare_calc_info,
            relative_eps=relative_eps,
            max_tries=max_tries,
            tests_runner=tests_runner,
            files_list=files_list,
            test_runner_folder=tests_runner_folder,
            report_file_path=errors_report_file_path,
        )

        pct_filters.append(pct_filter)

    remove_percentage_plot = RemovePercentageComparePlot(
        pct_filters=pct_filters,
        output_file=output_file,
        errors_report_file_path=errors_report_file_path,
    )

    ax1s = []
    ax2s = []
    for i in range(len(calc_infos_list)):
        row_start_idx = i * total_cols
        ax1s.append(axes_flat[row_start_idx + 1])
        ax2s.append(axes_flat[row_start_idx + 2])

    ax3s = []
    ax4s = []

    row3_start_idx = 2 * total_cols
    for col in range(total_cols):
        ax3s.append(axes_flat[row3_start_idx + col])

    row4_start_idx = 3 * total_cols
    for col in range(total_cols):
        ax4s.append(axes_flat[row4_start_idx + col])

    # remove_percentage_plot.draw(fig, ax1s, ax2s, ax3s, ax4s)

    num_of_iterations_boxplot = 5
    print(
        f"Running {num_of_iterations_boxplot} independent iterations for boxplot analysis..."
    )

    initial_errors_count = pct_filters[0].original_errors_count
    initial_test_count = pct_filters[0].total_files_count
    error_ids = sorted([error.error_id for error in initial_errors_count])

    boxplot_data = {}
    for error_id in error_ids:
        boxplot_data[error_id] = {"Initial": [], "LZMANCD": [], "EntropyNCD": []}

    for error in initial_errors_count:
        error_id = error.error_id
        percentage = (
            error.test_paths_count / initial_test_count if initial_test_count > 0 else 0
        )
        boxplot_data[error_id]["Initial"] = [percentage] * num_of_iterations_boxplot

    for iteration_num in range(num_of_iterations_boxplot):
        print(f"Running iteration {iteration_num + 1}/{num_of_iterations_boxplot}...")

        iteration_pct_filters = []
        for i in range(len(calc_infos_list)):
            main_calc_info = calc_infos_list[i]
            compare_calc_info = compare_calc_infos_list[i]

            iteration_pct_filter = RemovePercentageCompareFilter(
                main_calc_info=main_calc_info,
                compare_calc_info=compare_calc_info,
                relative_eps=relative_eps,
                max_tries=max_tries,
                tests_runner=tests_runner,
                files_list=files_list,
                test_runner_folder=tests_runner_folder,
                report_file_path=errors_report_file_path,
            )
            iteration_pct_filters.append(iteration_pct_filter)

        while not all(filter.is_finished for filter in iteration_pct_filters):
            for pct_filter in iteration_pct_filters:
                if not pct_filter.is_finished:
                    pct_filter.iterate()

        for i, pct_filter in enumerate(iteration_pct_filters):
            final_errors_count = pct_filter.errors_count_per_iteration[-1]
            current_test_count = len(pct_filter.current_indices)
            algo_name = pct_filter.main_calc_info.distances.algo.name

            error_lookup = {error.error_id: error for error in final_errors_count}

            for error_id in error_ids:
                if error_id in error_lookup:
                    error = error_lookup[error_id]
                    percentage = (
                        error.test_paths_count / current_test_count
                        if current_test_count > 0
                        else 0
                    )
                else:
                    percentage = 0.0

                boxplot_data[error_id][algo_name].append(percentage)

    ax_boxplot = axes_flat[4]
    ax_boxplot.clear()

    boxplot_values = []
    boxplot_labels = []
    boxplot_colors = []

    group_positions = []
    current_pos = 1

    for error_id in error_ids:
        group_positions.append((current_pos, current_pos + 1, current_pos + 2))

        if boxplot_data[error_id]["Initial"]:
            boxplot_values.append(boxplot_data[error_id]["Initial"])
            boxplot_labels.append("Initial")
            boxplot_colors.append("gray")

        if boxplot_data[error_id]["LZMANCD"]:
            boxplot_values.append(boxplot_data[error_id]["LZMANCD"])
            boxplot_labels.append("LZMA")
            boxplot_colors.append("royalblue")

        if boxplot_data[error_id]["EntropyNCD"]:
            boxplot_values.append(boxplot_data[error_id]["EntropyNCD"])
            boxplot_labels.append("Entropy")
            boxplot_colors.append("darkorange")

        current_pos += 4

    bp = ax_boxplot.boxplot(boxplot_values, patch_artist=True)

    for patch, color in zip(bp["boxes"], boxplot_colors):
        patch.set_facecolor(color)

    x_positions = []
    x_labels = []

    for i, error_id in enumerate(error_ids):
        group_start = group_positions[i][0]
        x_positions.extend([group_start, group_start + 1, group_start + 2])
        x_labels.extend(
            [f"{error_id}\nInitial", f"{error_id}\nLZMA", f"{error_id}\nEntropy"]
        )

    ax_boxplot.set_xticks(x_positions)
    ax_boxplot.set_xticklabels(x_labels, rotation=45, ha="right")

    for i, (start, mid, end) in enumerate(group_positions):
        if i < len(group_positions) - 1:
            ax_boxplot.axvline(x=end + 0.5, color="black", linestyle="--", alpha=0.3)

    ax_boxplot.set_xlabel("Error ID and Algorithm")
    ax_boxplot.set_ylabel("Percentage of test files with error")
    ax_boxplot.set_title(
        f"Error Percentage distribution across {num_of_iterations_boxplot} iterations"
    )
    ax_boxplot.grid(True, linestyle=":", linewidth=0.5, axis="y")

    save_plot_safely(fig, output_file)

    lzma_filter = pct_filters[0]
    filter_result = FilterResult(
        file_paths=lzma_filter.filtered_file_paths,
    )
    filter_result.save(
        report_pattern=report_pattern,
        range_start=0,
        range_end=1000,
        stage=0,
    )

    temp_dir.cleanup()

    # IterativePlotConfig(
    #     name="TDS Metric",
    #     texts=files_list.get_texts(),
    #     metric=TDSMetric(algo=),
    #     output_file=output_file,
    # ).execute()

    # TDSMetricPlot(
    #     files_list=files_list,
    #     metrics=[
    #         TDSMetric(algo=lzma_algo_compress),
    #         # TDSMetric(algo=entropy_algo_compress),
    #         # TDSMetric(algo=always_0),
    #         # TDSMetric(algo=always_1),
    #     ],
    #     output_file=output_file,
    # ).make_plot()


if __name__ == "__main__":
    main()
