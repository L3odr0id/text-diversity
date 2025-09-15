import argparse
import os
from textdistance import ZLIBNCD, EntropyNCD, RLENCD, Hamming, Jaccard
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass

from draw_plot import draw_all_plots


class Distances:
    def __init__(self, fdist: Callable[[str, str], float], algo_name: str):
        self._algo_name = algo_name
        self._fdist = fdist
        self._data: Dict[Tuple[int, int], Optional[float]] = {}

    def add_dist(self, prev_text: str, prev_idx: int, cur_text: str, cur_idx: int) -> None:
        try:
            distance_value = self._fdist(cur_text, prev_text)
        except Exception as e:
            print(f"Error calculating distance for pair ({prev_idx}, {cur_idx}): {e}")
            distance_value = None

        self._data[(prev_idx, cur_idx)] = distance_value

    def get_values(self) -> List[float]:
        return [v for v in self._data.values() if v is not None]

    def maxKey(self) -> int:
        all_indices = set()
        for (i, j) in self._data.keys():
            all_indices.add(i)
            all_indices.add(j)
        
        if not all_indices:
            raise ValueError("No distance data available")
        
        return max(all_indices)

    def find_minimax_center(self) -> Tuple[int, float, Dict[int, float]]:
        """
        Find the most centered text using minimax method.
        """
        num_texts = self.maxKey() + 1
        max_distances = {}

        # Max dist for all texts
        for i in range(num_texts):
            max_dist = 0.0
            for j in range(num_texts):
                if i != j:
                    if (j, i) in self._data and self._data[(j, i)] is not None:
                        dist = self._data[(j, i)]
                    elif (i, j) in self._data and self._data[(i, j)] is not None:
                        dist = self._data[(i, j)]
                    else:
                        raise ValueError(f"Distance ({i}, {j}) is not in storage")
                    
                    max_dist = max(max_dist, dist)
            
            max_distances[i] = max_dist
        
        # Find the index with minimum maximum distance
        center_idx = min(max_distances.keys(), key=lambda k: max_distances[k])
        min_max_distance = max_distances[center_idx]
        
        return center_idx, min_max_distance, max_distances
    
    def distance(self, fr: int, to: int):
        if (fr, to) in self._data and self._data[(fr, to)] is not None:
            dist = self._data[(fr, to)]
        elif (to, fr) in self._data and self._data[(to, fr)] is not None:
            dist = self._data[(to, fr)]
        else:
            raise f"Distance ({fr}, {to}) is not in storage"

        return dist
    
    def min_distance_from_last(self) -> Optional[float]:
        try:
            last_idx = self.maxKey()
        except ValueError:
            return 0.0

        if last_idx == 0:
            return 0.0  # только один текст

        min_d = float("inf")
        for i in range(last_idx):
            try:
                d = self.distance(last_idx, i)
                if d < min_d:
                    min_d = d
            except Exception:
                continue

        if min_d == float("inf"):
            return 0.0
        return min_d


@dataclass
class PlotSeries:
    name: str
    normalize: bool = True
    calc_function: Callable[[Distances], float] = None
    
    def calculate(self, storage: Distances) -> float:
        if self.calc_function is None:
            raise ValueError(f"Calculation function not defined for series: {self.name}")
        return self.calc_function(storage)


def calc_mean(values: List[float]) -> float:
    if not values:
        return float("nan")
    return float(np.array(values).mean())


def calc_median(values: List[float]) -> float:
    if not values:
        return float("nan")
    return float(np.median(values))


def calc_mean_metric(distances: Distances) -> float:
    values = distances.get_values()
    return calc_mean(values)


def calc_median_metric(distances: Distances) -> float:
    values = distances.get_values()
    return calc_median(values)


def calc_novelty_metric(distances: Distances) -> float:
    return distances.min_distance_from_last() or 0.0


def calc_sqrt_sum_squared_metric(distances: Distances) -> float:
    try:
        center_idx, _, _ = distances.find_minimax_center()
        return calc_custom_metric(distances, center_idx)
    except (ValueError, Exception):
        return float("nan")


def calc_custom_metric(distances: Distances, center_idx: int) -> float:
    num_texts = distances.maxKey() + 1
    if num_texts < 2:
        return float("nan")
    
    dists = []
    for i in range(num_texts):
        if i != center_idx:
            d = distances.distance(center_idx, i)
            dists.append(d)
            
    sum_sq = sum(d * d for d in dists)
    mean_sq = sum_sq / (len(dists) / 2) if dists else 0.0
    
    return mean_sq


# Configuration for Y series
PLOT_SERIES_CONFIG = [
    # PlotSeries(
    #     name="Mean distance",
    #     normalize=True,
    #     calc_function=calc_mean_metric
    # ),
    # PlotSeries(
    #     name="Median distance", 
    #     normalize=True,
    #     calc_function=calc_median_metric
    # ),
    PlotSeries(
        name="Novelty (min distance from last)",
        normalize=True,
        calc_function=calc_novelty_metric
    ),
    PlotSeries(
        name="Sqrt of sum squared",
        normalize=True,
        calc_function=calc_sqrt_sum_squared_metric
    )
]

def analyze_minimax(distance_storages: List[Distances], filenames: List[str]):
    print("\n" + "="*60)
    print("MINIMAX CENTER ANALYSIS")
    print("="*60)
    
    for storage in distance_storages:
        algo_name = storage._algo_name
        print(f"\nAlgorithm: {algo_name}")
        
        try:
            center_idx, min_max_distance, max_distances = storage.find_minimax_center()
            center_filename = filenames[center_idx]
        
            print(f"Most centered text: {center_filename}")
            print(f"Minimax distance: {min_max_distance:.4f}")
            print(f"Center index: {center_idx}")
            
            # Show top 5 most centered texts
            sorted_distances = sorted(max_distances.items(), key=lambda x: x[1])
            print(f"\nTop 5 most centered texts:")
            for i, (idx, max_dist) in enumerate(sorted_distances[:5]):
                filename = filenames[idx]
                print(f"  {i+1}. {filename} (max distance: {max_dist:.4f})")
                
        except Exception as e:
            print(f"Error in minimax analysis for {algo_name}: {e}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Text sets diversity utility")
    parser.add_argument("directory", help="Path to directory containing text files")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to analyze")
    args = parser.parse_args()

    directory = args.directory
    max_files = args.max_files

    filenames = [
        name for name in os.listdir(directory)
        if os.path.isfile(os.path.join(directory, name))
    ]
    filenames.sort()
    
    # Apply file limit if specified
    if max_files is not None:
        filenames = filenames[:max_files]

    algos = [
        ("ZLIBNCD", ZLIBNCD().distance),
        ("EntropyNCD", EntropyNCD().distance),
        ('Hamming', Hamming().distance),
        # ('RLENCD', RLENCD().distance),
        ('Jaccard', Jaccard().distance)
    ]

    distance_storages: List[Distances] = [
        Distances(algo_func, algo_name=algo_name) for algo_name, algo_func in algos
    ]

    x_values: list[int] = []

    series_data = {}
    for series in PLOT_SERIES_CONFIG:
        series_data[series.name] = {name: [] for name, _ in algos}

    file_contents = {}
    for file_idx, name in enumerate(filenames):
        path = os.path.join(directory, name)
        print(f"[+] Reading {name}")
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_contents[name] = f.read()
            
            # Calculate distances between current file and all previous files for each algorithm
            current_text = file_contents[name]
            for prev_idx in range(file_idx):
                prev_text = file_contents[filenames[prev_idx]]
                for storage in distance_storages:
                    storage.add_dist(prev_text, prev_idx, current_text, file_idx)
            
            # Calculate statistics for current iteration
            x_values.append(file_idx + 1)
            for storage in distance_storages:
                algo_name = storage._algo_name
                
                for series in PLOT_SERIES_CONFIG:
                    try:
                        value = series.calculate(storage)
                        series_data[series.name][algo_name].append(value)
                        
                        print(f'{series.name} ({algo_name}): {value:.4f}')
                        
                    except Exception as e:
                        print(f'Error calculating {series.name} for {algo_name}: {e}')
                        series_data[series.name][algo_name].append(float("nan"))
            
            if x_values:
                plots = [
                    (series.name, series_data[series.name], series.normalize)
                    for series in PLOT_SERIES_CONFIG
                ]
                draw_all_plots(x_values=x_values, plots=plots, title="Distance vs Number of Files", output_path="ncd_stats_plots.png")
        except Exception as e:
            print(f"Error reading {name}: {e}")


if __name__ == "__main__":
    main()
