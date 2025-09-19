import argparse
import math
import os
import random
from typing import List, Tuple, Callable

from scipy.stats import poisson
from textdistance import EntropyNCD, LZMANCD, ArithNCD

from texts_diversity import (
    Distances, 
    PlotConfig, 
    Algo,
    analyze_text_diversity
)

from common_distances import always_0, always_1
from common_normalization import min_max_normalization
from common_metrics import calc_mean_metric

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

def calc_mean_sqrt_sum_squared_metric(distances: Distances) -> float:
    distance_values = distances.get_values()
    sum_squared = sum(distance * distance for distance in distance_values)
    mean_sum_squared = sum_squared / len(distance_values)
    return math.sqrt(mean_sum_squared)

def calc_mean_sqrt_sum_squared_metric_from_minimax_center(distances: Distances) -> float:
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

def calc_poisson_distribution(distances: Distances) -> float:
    distance_values = distances.get_values()
    distance_values.sort()
    values = []
    for i in range(len(distance_values)):
        value = 2 * distance_values[i] * poisson.pmf(i, len(distance_values))
        values.append(value)
    return sum(values)
    
def calc_poisson_distribution_plus_1_minus_always_1(distances: Distances) -> float:
    poisson_value = calc_poisson_distribution(distances=distances)
    always_1_dist = Distances(distance_func=always_1, algo_name="Always 1")
    always_1_dist._data = {(i, j): 1 for (i, j) in distances._data}
    always_1_poisson = calc_poisson_distribution(distances=always_1_dist)
    return poisson_value + 1 - always_1_poisson


PLOT_CONFIGS = [
    # PlotConfig(
    #     name="Mean distance",
    #     metric=calc_mean_metric,
    #     normalize_algorithms=[]
    # ),
    # PlotConfig(
    #     name="Mean sqrt of sum squared",
    #     metric=calc_mean_sqrt_sum_squared_metric,
    #     normalize_algorithms=[]
    # ),
    PlotConfig(
        name="Mean sqrt of sum squared from minimax center", 
        metric=calc_mean_metric,
        normalize_algorithms=["EntropyNCD * 5"]
    ),
]

algos = [
    # Algo("ZLIBNCD", ZLIBNCD().distance),
    # Algo('EntropyNCD', EntropyNCD().distance),
    # Algo('LZMANCD', LZMANCD().distance),
    Algo('EntropyNCD * 5', custom_entropy, normalize=min_max_normalization),
    Algo('EntropyNCD * 5 not normal', custom_entropy),
    Algo('Always 0', always_0),
    Algo('Always 1', always_1),
]

def main() -> None:
    parser = argparse.ArgumentParser(description="Text sets diversity utility")
    parser.add_argument("directory", help="Path to directory containing text files")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to analyze")
    parser.add_argument("--output", type=str, help="Name of the output plot file", default="ncd_stats_plots.png")
    parser.add_argument("--shuffle", action="store_true", help="Randomly shuffle filenames instead of sorting them")
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files
    output_file = args.output
    shuffle = args.shuffle

    filenames = [
        name for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
    ]
    
    if shuffle:
        random.shuffle(filenames)
    else:
        filenames.sort()
    
    if max_files is not None:
        filenames = filenames[:max_files]

    file_paths = [os.path.join(directory, name) for name in filenames]

    analyze_text_diversity(
        file_paths=file_paths,
        plot_configs=PLOT_CONFIGS,
        algos=algos,
        output_file=output_file
    )


if __name__ == "__main__":
    main()
