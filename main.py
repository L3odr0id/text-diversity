import argparse
import math
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
from TDSMetric import TDSMetric
from remove_percentage_compare_metric import RemovePercentageCompareFilter
from remove_percentage_compare_plot import RemovePercentageComparePlot
from TDS_metric_plot import TDSMetricPlot


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


lzma_algo_compress = CompressAlgo(name="LZMA", func=lzma_compress)


def entropy_compress(text: str) -> bytes:
    return EntropyNCD()._compress(bytes(text, "utf-8"))


entropy_algo_compress = CompressAlgo(name="Entropy", func=entropy_compress)

lzma_algo = Algo("LZMANCD", LZMANCD().distance)
entropy_algo = Algo("EntropyNCD", EntropyNCD().distance)
entropy_algo_x5 = Algo("EntropyNCD * 5", custom_entropy)
poisson_metric = Metric("Poisson_dist", calc_poisson_distribution)
poisson_mins_metric = Metric("Poisson_mins", calc_poisson_mins)


def filters_list_for_each(
    calc_infos: List[CalcInfo],
    files_list: FilesList,
    eps: float,
    max_tries: int,
) -> List[RemovePercentageCompareFilter]:
    return [
        RemovePercentageCompareFilter(
            calc_info=calc_info,
            eps=eps,
            max_tries=max_tries,
            initial_texts=files_list.get_texts(),
        )
        for calc_info in calc_infos
    ]


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
        "--add-filter-plot",
        action="store_true",
        help="Add remove percentage filter plot",
    )
    parser.add_argument(
        "--test-runner-output-path",
        type=str,
        help="Path to the output of the test runner",
    )
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files
    output_file = args.output
    shuffle = args.shuffle
    add_filter_plot = args.add_filter_plot
    test_runner_output_path = args.test_runner_output_path
    files_list = FilesList(dir=directory, shuffle=shuffle, max_files=max_files)

    # levenshtein_distance_normalized = LevenshteinDistanceNormalized(
    #     files_list=files_list
    # )
    # levenshtein_distance_normalized_algo = Algo(
    #     "Levenshtein Normalized Distance", levenshtein_distance_normalized.distance
    # )

    calc_infos = cis_same_metric(
        algos=[
            Algo("EntropyNCD * 5", custom_entropy),
            Algo("EntropyNCD", EntropyNCD().distance),
            Algo("LZMANCD", LZMANCD().distance),
            Algo("Always 0", always_0),
            Algo("Always 1", always_1),
        ],
        metric=lambda: Metric(name="Poisson_dist", calc=calc_poisson_distribution),
    )

    plot_configs = [
        # PlotConfig(
        #     name="Mean distance vs number of files",
        #     calc_infos=cis_same_metric(
        #         algos=[
        #             # Algo("EntropyNCD * 5", custom_entropy),
        #             # Algo("EntropyNCD", EntropyNCD().distance),
        #             # Algo("LZMANCD", LZMANCD().distance),
        #             # levenshtein_distance_normalized_algo,
        #             Algo("Always 0", always_0),
        #             Algo("Always 1", always_1),
        #         ],
        #         metric=lambda: Metric(name="Min Distance", calc=calc_mean_metric),
        #     ),
        # ),
        # PlotConfig(
        #     name="Min distance vs number of files",
        #     calc_infos=cis_same_metric(
        #         algos=[
        #             Algo("EntropyNCD * 5", custom_entropy),
        #             Algo("EntropyNCD", EntropyNCD().distance),
        #             Algo("LZMANCD", LZMANCD().distance),
        #             Algo("Always 0", always_0),
        #             Algo("Always 1", always_1),
        #         ],
        #         metric=lambda: Metric(
        #             name="Min Distance", calc=MinDistanceMetric().calc
        #         ),
        #     ),
        # ),
        # PlotConfig(
        #     name="Mean distance plot",
        #     calc_infos=[
        #         CalcInfo(
        #             metric=Metric(name="Add min distance", calc=MinDistanceMetric().calc),
        #             algo=Algo("EntropyNCD * 5", custom_entropy),
        #         ),
        #         CalcInfo(
        #             metric=Metric(name="Add min distance", calc=MinDistanceMetric().calc),
        #             algo=Algo("EntropyNCD", EntropyNCD().distance),
        #         ),
        #         CalcInfo(
        #             metric=Metric(name="Add min distance", calc=MinDistanceMetric().calc),
        #             algo=Algo("LZMANCD", LZMANCD().distance),
        #         ),
        #         CalcInfo(
        #             metric=Metric(name="Add min distance", calc=MinDistanceMetric().calc),
        #             algo=Algo("Always 0", always_0),
        #         ),
        #         CalcInfo(
        #             metric=Metric(name="Add min distance", calc=MinDistanceMetric().calc),
        #             algo=Algo("Always 1", always_1),
        #         ),
        #     ],
        # ),
        # PlotConfig(
        #     name="Min distance vs number of files",
        #     calc_infos=cis_same_metric(
        #         algos=[
        #             Algo("EntropyNCD", EntropyNCD().distance),
        #         ],
        #         metric=lambda: Metric(
        #             name="Min Distance", calc=MinDistanceMetric().calc
        #         ),
        #     ),
        # ),
        PlotConfig(
            name="Poisson_mins distance vs number of files",
            calc_infos=calc_infos,
        ),
    ]

    num_plot_configs = len(plot_configs)
    if add_filter_plot:
        total_axes = num_plot_configs + 3
    else:
        total_axes = num_plot_configs

    fig, axes = plt.subplots(1, total_axes, figsize=(6 * total_axes, 6))
    if total_axes == 1:
        axes = [axes]

    plot_configs_axes = axes[:num_plot_configs]

    TextsDiversity(
        min_files_for_analysis=10,
        files_list=files_list,
        plots_list=PlotsList(
            configs=plot_configs,
            title="Plots list title",
            output_file=output_file,
            fig=fig,
            axes=plot_configs_axes,
        ),
    ).draw_plots()

    if add_filter_plot:
        remove_percentage_plot = RemovePercentageComparePlot(
            filters=filters_list_for_each(
                calc_infos=calc_infos,
                files_list=files_list,
                eps=0.001,
                max_tries=10,
            ),
            output_file=output_file,
            test_runner_output_path=test_runner_output_path,
        )

        remove_percentage_axes = axes[num_plot_configs:]
        remove_percentage_plot.draw(
            fig,
            remove_percentage_axes[0],
            remove_percentage_axes[1],
            remove_percentage_axes[2],
        )

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
